from dotenv import load_dotenv
load_dotenv()

from app.modules.whatsapp_tool import whatsapp_template_tool

payload = '{"1":"12/1","2":"3pm"}'
result = whatsapp_template_tool.run(payload)
print(result)
