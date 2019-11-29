import smtplib
from contextlib import contextmanager
from dataclasses import dataclass, field
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate
from os.path import basename
from pathlib import Path
from smtpd import COMMASPACE
from typing import List, Dict, ClassVar


@dataclass
class EmailMessage:
    encoding: ClassVar[str] = 'utf8'

    subject: str = ''
    body: str = ''
    from_email: str = ''
    password: str = ''
    to: List[str] = field(default_factory=list)
    server: str = ''

    attachments: List[str] = field(default_factory=list)
    headers: Dict = field(default_factory=dict)
    connection = None

    @contextmanager
    def connect(self):
        if not self.connection:
            if all([self.from_email, self.password, self.server]):
                smtp = smtplib.SMTP(self.server)
                smtp.login(self.from_email, self.password)
                self.connection = smtp
            else:
                raise ValueError('Login info miss, you must init with from, pswd and server')
        yield self.connection
        self.connection.close()

    def init_message(self):
        msg = MIMEMultipart()
        msg['From'] = self.from_email
        msg['To'] = COMMASPACE.join(self.to)
        msg['Date'] = formatdate(localtime=True)
        msg['Subject'] = self.subject
        msg.attach(MIMEText(self.body))
        return msg

    def init_attachments(self, msg):
        """
        Prepare attachments in self.attachments
        :param msg: return by self.init_message()
        """
        for f in self.attachments:
            f = Path(f)
            part = MIMEApplication(f.read_bytes(), f.name)
            part['Content-Disposition'] = 'attachment; filename="%s"' % basename(f)
            msg.attach(part)

    def send(self):
        msg = self.init_message()

        if self.attachments:
            self.init_attachments(msg)

        with self.connect() as email:
            email.sendmail(self.from_email, self.to, msg.as_string())

    def attach(self, *files):
        self.attachments.extend(files)
