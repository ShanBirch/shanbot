import markdown
from datetime import datetime

# Read the markdown file
with open('Facebook_Ads_Plan_Vegan_Challenge.md', 'r', encoding='utf-8') as f:
    md_content = f.read()

# Replace {current_date} with actual date
current_date = datetime.now().strftime('%B %d, %Y')
md_content = md_content.replace('{current_date}', current_date)

# Convert markdown to HTML
html_content = markdown.markdown(md_content)

# Create a complete HTML document with CSS styling
html_doc = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Facebook Ads Strategy Plan - Vegan Challenge</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background: white;
        }}
        h1 {{
            color: #7B2CBF;
            border-bottom: 3px solid #7B2CBF;
            padding-bottom: 10px;
            text-align: center;
        }}
        h2 {{
            color: #9D4EDD;
            margin-top: 30px;
            margin-bottom: 15px;
        }}
        h3 {{
            color: #C77DFF;
            margin-top: 25px;
        }}
        strong {{
            color: #5A189A;
        }}
        ul, ol {{
            padding-left: 20px;
        }}
        li {{
            margin-bottom: 5px;
        }}
        hr {{
            border: none;
            border-top: 2px solid #E0AAFF;
            margin: 30px 0;
        }}
        .highlight {{
            background-color: #F3E8FF;
            padding: 15px;
            border-left: 4px solid #7B2CBF;
            margin: 20px 0;
        }}
        @media print {{
            body {{
                font-size: 12px;
            }}
            h1 {{
                font-size: 24px;
            }}
            h2 {{
                font-size: 18px;
            }}
            h3 {{
                font-size: 16px;
            }}
        }}
    </style>
</head>
<body>
{html_content}
</body>
</html>'''

# Write HTML to file
with open('Facebook_Ads_Plan_Vegan_Challenge.html', 'w', encoding='utf-8') as f:
    f.write(html_doc)

print('HTML file created successfully!')
print('To convert to PDF:')
print('1. Open Facebook_Ads_Plan_Vegan_Challenge.html in your browser')
print('2. Press Ctrl+P (or Cmd+P on Mac)')
print('3. Choose "Save as PDF" as the destination')
print('4. Save as "Facebook_Ads_Plan_Vegan_Challenge.pdf"')

