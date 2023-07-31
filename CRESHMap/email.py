import smtplib
from email.message import EmailMessage

email_message = '''
Dear CRESHMap User,

Thank you for your interest in the Cresh Map data set. You can download the data set by clicking on the link below:

https://{tldn}/download/{dl_hash}

Best regards
www.creshmap.com
'''

def send_download_link(from_address, smtp_server, name, to_address, dl_hash, tldn):

    msg_text = email_message.format(dl_hash=dl_hash, tldn=tldn, name=name)

    msg = EmailMessage()
    msg.set_content(msg_text)

    msg['Subject'] = 'Cresh Map data download link'
    msg['From'] = from_address
    msg['To'] = to_address

    with smtplib.SMTP(smtp_server) as server:
        server.send_message(msg)
