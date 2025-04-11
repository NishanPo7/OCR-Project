import numpy as np
import pandas as pd
import cv2
import pytesseract
import spacy
import re
import string
import warnings
warnings.filterwarnings('ignore')

# Load NER Model
model_ner = spacy.load('./output/model-best/')

def cleanText(txt):
    whitespace = string.whitespace
    punctuation = '!"#$%&\'()*+,:;<=>?@[\\]^_`{|}~'  # Keep hyphens (-)
    tableWhitespace = str.maketrans('','',whitespace)
    tablePunctuation = str.maketrans('','',punctuation)
    text = str(txt)
    text = text.lower()
    removewhitespace = text.translate(tableWhitespace)
    removepunctuation = removewhitespace.translate(tablePunctuation)
    return str(removepunctuation)

class groupgen():
    def __init__(self):
        self.id = 0
        self.text = ''
    def getgroup(self, text):
        if self.text == text:
            return self.id
        else:
            self.id +=1
            self.text = text
            return self.id

def parser(text, label):
    if label == 'NAME':
        text = text.lower().title()    
    elif label == 'SUB':
        text = text.lower().title()
    elif label == 'RES':
        text = text.upper()
    return text

grp_gen = groupgen()

def getPredictions(image):
    # Define ROIs (bounding box coordinates)
    rois = [
        (769, 840, 362, 1041),  # ROI 1
        (853, 916, 406, 700),  # ROI 2
        (853, 915, 1632, 2022),  # ROI 3
        (1331, 1472, 483, 748),  # s1
        (1328, 1453, 1850, 1966),  # ROI 4
        (1500, 1576, 489, 769),   # s2
        (1475, 1588, 1850, 1966),  # ROI 5
        (1630, 1707, 492, 729),    # s3
        (1612, 1728, 1851, 1965),  # ROI 6
        (1768, 1841, 488, 741),    # s4
        (1745, 1863, 1852, 1965),  # ROI 7
        (1923, 1988, 487, 645),    # s5
        (1882, 2004, 1853, 1967),  # ROI 8
        (2537, 2606, 1857, 1974),  # ROI 9
        (2729, 2794, 368, 571),    # ROI 10
    ]
    
    roi_dataframes = []
    
    for i, (y1, y2, x1, x2) in enumerate(rois):
        # Crop the ROI from the image
        roi = image[y1:y2, x1:x2]
        data = pytesseract.image_to_data(roi, lang='eng', output_type=pytesseract.Output.DATAFRAME)
        roi_dataframes.append(data)
    
    # Concatenate all DataFrames into one
    final_df = pd.concat(roi_dataframes, ignore_index=True)
    final_df.dropna(inplace=True)  # Drop missing values
    final_df['text'] = final_df['text'].apply(cleanText)
    
    # Clean and prepare text
    df_clean = final_df.query('text != "" ')
    content = " ".join([w for w in df_clean['text']])
    print("OCR Content:", content)  # Debug print
    
    # REGEX Fallback for Registration Number
    reg_pattern = r'\d+-\d+-\d+-\d+-\d+'
    reg_match = re.search(reg_pattern, content)
    reg_number = [reg_match.group()] if reg_match else []
    
    # Get predictions from the NER model
    doc = model_ner(content)
    
    # Convert predictions to JSON
    docjson = doc.to_json()
    doc_text = docjson['text']
    
    # Tokenize the text
    datafram_tokens = pd.DataFrame(docjson['tokens'])
    datafram_tokens['token'] = datafram_tokens[['start', 'end']].apply(
        lambda x: doc_text[x[0]:x[1]], axis=1
    )
    
    # Extract labels
    right_table = pd.DataFrame(docjson['ents'])[['start', 'label']]
    datafram_tokens = pd.merge(datafram_tokens, right_table, how='left', on='start')
    datafram_tokens.fillna('O', inplace=True)
    
    # Join tokens and labels with the cleaned DataFrame
    df_clean['end'] = df_clean['text'].apply(lambda x: len(x) + 1).cumsum() - 1
    df_clean['start'] = df_clean[['text', 'end']].apply(lambda x: x[1] - len(x[0]), axis=1)
    dataframe_info = pd.merge(df_clean, datafram_tokens[['start', 'token', 'label']], how='inner', on='start')
    
    # Handle bounding box information
    bb_df = dataframe_info.query("label != 'O' ")
    bb_df['label'] = bb_df['label'].apply(lambda x: x[2:])
    bb_df['group'] = bb_df['label'].apply(grp_gen.getgroup)

    # Calculate right and bottom of bounding box
    bb_df[['left','top','width','height']] = bb_df[['left','top','width','height']].astype(int)
    bb_df['right'] = bb_df['left'] + bb_df['width']
    bb_df['bottom'] = bb_df['top'] + bb_df['height']
    
    # Group and merge bounding box data
    col_group = ['left', 'top', 'right', 'bottom', 'label', 'token', 'group']
    group_tag_img = bb_df[col_group].groupby(by='group')
    img_tagging = group_tag_img.agg({
        'left': min,
        'right': max,
        'top': min,
        'bottom': max,
        'label': np.unique,
        'token': lambda x: " ".join(x)
    })
    
    # Parse entities with improved logic
    entities = {
        'NAME': [], 
        'ROLL': [], 
        'REG': reg_number,
        'SUB': [], 
        'SS': [], 
        'TS': [], 
        'RES': []
    }
    
    # Additional NER model entity extraction
    current_entity = {'text': '', 'label': None}
    for ent in doc.ents:
        if ent.label_ == 'REG' and reg_number:
            continue  # Skip if already captured by regex
        if ent.label_ in entities:
            parsed_text = parser(ent.text, ent.label_)
            entities[ent.label_].append(parsed_text)

    # Fallback to token-based extraction for other entities
    for _, row in dataframe_info.iterrows():
        token = row['token']
        label = row['label']
        
        if label == 'O' or not token:
            continue
            
        bio_tag = label[0]
        label_type = label[2:]
        
        parsed_token = parser(token, label_type)
        
        # Only process if not already captured by regex or doc.ents
        if label_type == 'REG' and reg_number:
            continue
            
        if bio_tag == 'B':
            if label_type in entities:
                entities[label_type].append(parsed_token)
        elif bio_tag == 'I':
            if label_type in entities and entities[label_type]:
                entities[label_type][-1] += f" {parsed_token}"

    return image, entities