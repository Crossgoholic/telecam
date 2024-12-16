import imaplib
import asyncio
import os
import email
from telegram import Bot
import os
import time
from dotenv import load_dotenv


DEBUG = False
load_dotenv()

def _imapConnect(host:str, port:int, email:str, password:str) -> imaplib.IMAP4_SSL:
    session = imaplib.IMAP4_SSL(host, port)
    if session:
        try:
            session.login(email, password)
            return session
        except:
            raise 
    else:
        raise "Connection Error"

async def sendCamVideo(videofile: bytes, caption: str, chatID: int) -> bool:
    bot = Bot(token=os.getenv("TELEGRAMAPIKEY"))
    async with bot:
        await bot.send_video(video=videofile,caption=caption,chat_id=chatID)
        #await bot.send_message(chat_id=chatID, text=caption)

async def getEmails(session:imaplib.IMAP4_SSL) -> list:
    task = []
    session.select("Inbox")
    typ, data = session.search(None, (f'TO "{os.getenv("EMAIL")}"'))
    for num in data[0].split():
        typ, data = session.fetch(num, '(RFC822)')
        rawEmail = data[0][1]
        rawEmailString = rawEmail.decode("utf-8")
        emailMessage = email.message_from_string(rawEmailString)
        for part in emailMessage.walk():
            if part.get_content_maintype() == 'multipart':
                continue
            if part.get('Content-Disposition') is None:
                continue
            fileName = part.get_filename()
            task = asyncio.create_task(sendCamVideo(videofile=part.get_payload(decode=True),
                         caption=fileName,
                         chatID=os.getenv("CHATID")))
            await task
        session.store(num, '+FLAGS', '\\Deleted')
    session.expunge()
    session.close()
       
while True:
    session = _imapConnect(host=os.getenv("HOST"),
                       port=os.getenv("PORT"),
                       email=os.getenv("EMAIL"),
                       password=os.getenv("PASSWORD"))
    emails = asyncio.run(getEmails(session=session))
    session.logout()
    time.sleep(5)    
