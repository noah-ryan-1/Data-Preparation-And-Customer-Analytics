import pandas as pd
pd.plotting.register_matplotlib_converters()
import matplotlib.pyplot as plt  
import seaborn as sns 

'''
SECTION 1: FILE READING
'''

transaction_path = '/Users/noahpeter/Desktop/VSCodeDirectory/Chip_Analysis/Data/QVI_transaction_data.csv'
purchase_path = '/Users/noahpeter/Desktop/VSCodeDirectory/Chip_Analysis/Data/QVI_purchase_behaviour.csv'

# File Readings 
transaction = pd.read_csv(transaction_path, sep=';', decimal=',')
purchase = pd.read_csv(purchase_path)

'''
SECTION 2: DATA CLEANING
'''

# Ammending Date Column
transaction.DATE = pd.to_datetime(transaction.DATE, unit='D', origin='1899-12-30')


# Removing Salsas + Chutneys
undesired = ['salsa', 'chutny']
def remove(line):
    for word in undesired:
        if word in line.lower():
            return False
    return True
            
transaction = transaction[transaction.PROD_NAME.apply(remove)]

# Removing outliers
transaction = transaction[transaction['LYLTY_CARD_NBR'] != 226000].reset_index(drop=True)

# Sorting into Pack Size and merging datasets
pack_sizes = pd.Series(list([int(line.lower()[-4:-1])
                             if line[-4:-1].isdigit()
                             else int(line.lower()[-3:-1]) if line[-3:-1].isdigit()
                             else int(line.lower()[7:10]) 
                             for line in transaction['PROD_NAME'] 
                             ]), name='PACK_SIZE')

transaction = transaction.join(pack_sizes)                       


# Sorting into Brand Name
corrections = {'Dorito': 'Doritos', 'Infzns': 'Infuzions', 'Smith':'Smiths', 'Natural':'NCC', 'Grain':'GrnWves', 
               'Red':'RRD', 'Snbts':'Sunbites' }

transaction['BRAND'] = (transaction['PROD_NAME'].str.split().str[0].replace(corrections))

# Sorting into Flavor (remaining piece of information left in PROD_NAME)
removables = {'Chips', 'Popd', 'Plus', 'Whlegrn', 'Crisps', 'Crinkle', 'Cut', 'Fries', 'Potato', 
              'ChipCo', 'Chip', 'Compny', 'Corn', 'Strws', 'Thinly', 'Waves', 'Chipco', 'D/Style', 
              'Stacked', 'Sensations', 'PotatoMix', 'Crackers', 'Tortilla', 'Balls', 'Puffs', 
              'Crn Crnchers', 'Pc', 'Rock Deli', 'Whlgrn', 'SR', 'Co'}

def filter_flavor(line):
    ''' Takes in a line a removes any of the above undesired phrases or trailing weights'''
    words = line.split()[1:] # Removes First Word which is the company
    cleaned_words = []
    for word in words:
        mod_word = []
        for char in word:
            if char.isdigit():
                break
            mod_word.append(char)
        clean_word = ''.join(mod_word)
        if clean_word and clean_word not in removables:
            cleaned_words.append(clean_word)
    return ' '.join(cleaned_words)
            

transaction.PROD_NAME = transaction.PROD_NAME.apply(filter_flavor)
# Renaming the Column to Flavors
transaction = transaction.rename(columns={'PROD_NAME':'Flavor'})


'''
SECTION 3: Integrating Datasets
'''

master_dataset = pd.merge(transaction, purchase, on='LYLTY_CARD_NBR', how='left')

# Replace Lifestage Names for Readability
replace_dict = {'YOUNG SINGLES/COUPLES':'Young S/C', 
                'MIDAGE SINGLES/COUPLES':'Midage S/C', 
                'OLDER SINGLES/COUPLES':'Older S/C',
                'RETIREES':'Retirees', 
                'OLDER FAMILIES': 'Older Families', 
                'YOUNG FAMILIES': 'Young Families', 
                'NEW FAMILIES': 'New Families'}
master_dataset['LIFESTAGE'] = master_dataset['LIFESTAGE'].replace(replace_dict)

# Saving Cleaned Data: 
master_dataset.to_csv('cleaned_data.csv', index=False)


'''
SECTION 4: Analysis Preparation: 
'''

# Sales Data: 
stage_expenditure = master_dataset.loc[:,['LIFESTAGE', 'TOT_SALES', 'PREMIUM_CUSTOMER']].copy()
cumulative = stage_expenditure.loc[:,['LIFESTAGE', 'TOT_SALES']].groupby('LIFESTAGE').sum() / 1000
split = stage_expenditure.groupby(['LIFESTAGE', 'PREMIUM_CUSTOMER']).sum() / 1000

#  Customers per Segment 

segment_counts = (
    master_dataset[['LYLTY_CARD_NBR','LIFESTAGE' ,'PREMIUM_CUSTOMER']]
    .drop_duplicates(subset=['LYLTY_CARD_NBR'])
    .groupby(['LIFESTAGE', 'PREMIUM_CUSTOMER'])
    .size()
    .reset_index(name='COUNT'))

# Focus on Cumulatives
cumulative_group = segment_counts[['LIFESTAGE', 'COUNT']].groupby('LIFESTAGE').sum().reset_index()

total_customers = segment_counts['COUNT'].sum()

# Selecting Seaborn Colors: 
colors = sns.color_palette('pastel')[0:len(cumulative_group)]

# Creating labels for counts and percentages: 
labels = [f"{row['LIFESTAGE']}\n {row['COUNT']} ({row['COUNT']/total_customers:.1%})"
            for _, row in cumulative_group.iterrows()]


'''
Section 5: Visualisation Code (Uncomment to Use Sections)
'''


# 1.1: Graphing Cumulative Bar Graph
# plt.figure(figsize=(10,6))
# plt.title('Total Chip Purchases by Customer Lifestage Group')
# sns.barplot(data=cumulative, x='LIFESTAGE', y='TOT_SALES', errwidth=0)
# plt.xlabel('Customer Life Stage Groups')
# plt.ylabel('Total Expenditure by Group (Thousand)')
# plt.show()

# 1.2: Graphing Premium Split Bar Graphs
# plt.figure(figsize=(10,6))
# plt.title('Total Chip Purchases by Customer Lifestage Group')
# sns.barplot(data=stage_expenditure, x='LIFESTAGE', y='TOT_SALES', hue='PREMIUM_CUSTOMER', 
#              palette='viridis', saturation=0.8, errwidth=0)
# plt.xlabel('Customer Life Stage Groups')
# plt.ylabel('Total Expenditure by Group (Thousand)')
# plt.legend(title='Customer Type')
# plt.show()

# 2.1: Pie Chart Customer Type Categories: 
# plt.figure(figsize=(8,8))
# plt.pie(cumulative_group['COUNT'], 
#         labels=labels, 
#         colors=colors, 
#         autopct='%.1f%%', 
#         startangle=90,
#         wedgeprops={'linewidth':1, 'edgecolor':'white'})
# plt.annotate(f'Total Customers: {total_customers}',
#              xy = (0.95, -1.1),
#              ha='center',
#              fontsize=12,
#              weight='bold')
# plt.title('Total Customers By Lifestage', fontsize=14)
# sns.despine()
# plt.tight_layout()
# plt.show()

# 2.2: Plotting Seggregated Categories of Customer Type:
# plt.figure(figsize=(10,6))
# sns.barplot(data=segment_counts, x='LIFESTAGE', y='COUNT', hue='PREMIUM_CUSTOMER', palette='viridis')
# plt.title('Total Customers by Lifestage and Customer Type')
# plt.xlabel('Customer Lifestage')
# plt.ylabel('No. of Customers')
# plt.legend(title='Customer Type')
# plt.show()









