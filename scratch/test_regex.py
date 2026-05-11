import re

ai_text = "أنصحك بلابتوب ديل بـ 6200 شيكل، رامات 16 وهارد 512، وسعره 6000 كمان اذا بدك خصم. السعر 5500 شاقل."
price_pattern = r'(?:سعر|بـ|سعره|ب)\s*(\d+(?:,\d+)?)|(\d+(?:,\d+)?)\s*(?:شيكل|شاقل)'
matches = re.findall(price_pattern, ai_text)

print("Matches:", matches)

mentioned_numbers = []
for match in matches:
    num_str = match[0] if match[0] else match[1]
    try:
        val = int(num_str.replace(',', ''))
        mentioned_numbers.append(val)
    except:
        pass
        
print("Mentioned prices:", mentioned_numbers)
