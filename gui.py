import sys
import time
from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QTextEdit, QMessageBox, QScrollArea
)
from PyQt5.QtCore import QTimer
from instagrapi import Client
from instagrapi.exceptions import ClientError

class InstagramBotGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ربات اینستاگرام - پدیده")
        self.setGeometry(100, 100, 500, 800)

        # ورودی‌ها
        self.username_input = QLineEdit()
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)

        self.limit_input = QLineEdit()
        self.limit_input.setPlaceholderText("تعداد فعالیت در روز (مثلاً 10)")

        self.replies_input = QTextEdit()
        self.replies_input.setPlaceholderText("پاسخ‌های خودکار به دایرکت/کامنت (هر خط یک پیام)")

        self.hashtags_input = QTextEdit()
        self.hashtags_input.setPlaceholderText("هشتگ‌ها یا پیج‌های هدف برای لایک/کامنت (هر خط یک هشتگ/پیج)")

        self.comment_input = QLineEdit()
        self.comment_input.setPlaceholderText("متن کامنت خودکار")

        self.trigger_comment_input = QLineEdit()
        self.trigger_comment_input.setPlaceholderText("کامنت فعال‌کننده (مثلاً: کد تخفیف)")

        self.follow_reply_input = QLineEdit()
        self.follow_reply_input.setPlaceholderText("پیام وقتی هنوز فالو نکرده")

        self.success_reply_input = QLineEdit()
        self.success_reply_input.setPlaceholderText("پیام وقتی فالو کرده")

        # لاگ برای نمایش وضعیت و خطاها
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setPlaceholderText("وضعیت و خطاها اینجا نمایش داده می‌شود...")

        # دکمه‌ها
        self.login_button = QPushButton("ورود به حساب")
        self.logout_button = QPushButton("خروج از حساب")
        self.logout_button.setEnabled(False)

        self.like_comment_button = QPushButton("فعال کردن لایک و کامنت خودکار")

        # اتصال سیگنال‌ها
        self.login_button.clicked.connect(self.login)
        self.logout_button.clicked.connect(self.logout)
        self.like_comment_button.clicked.connect(self.toggle_auto_like_comment)

        # لایه‌بندی
        layout = QVBoxLayout()
        layout.addWidget(QLabel("نام کاربری:"))
        layout.addWidget(self.username_input)
        layout.addWidget(QLabel("رمز عبور:"))
        layout.addWidget(self.password_input)
        layout.addWidget(QLabel("تعداد فعالیت در روز:"))
        layout.addWidget(self.limit_input)
        layout.addWidget(QLabel("پاسخ‌های خودکار به دایرکت/کامنت (هر خط یک پیام):"))
        layout.addWidget(self.replies_input)
        layout.addWidget(QLabel("هشتگ‌ها یا پیج‌های هدف برای لایک/کامنت (هر خط یک هشتگ یا پیج):"))
        layout.addWidget(self.hashtags_input)
        layout.addWidget(QLabel("متن کامنت خودکار:"))
        layout.addWidget(self.comment_input)
        layout.addWidget(QLabel("کامنت فعال‌کننده:"))
        layout.addWidget(self.trigger_comment_input)
        layout.addWidget(QLabel("پیام وقتی هنوز فالو نکرده:"))
        layout.addWidget(self.follow_reply_input)
        layout.addWidget(QLabel("پیام وقتی فالو کرده:"))
        layout.addWidget(self.success_reply_input)
        layout.addWidget(QLabel("لاگ وضعیت:"))
        layout.addWidget(self.log_text)

        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(self.login_button)
        buttons_layout.addWidget(self.logout_button)
        buttons_layout.addWidget(self.like_comment_button)

        layout.addLayout(buttons_layout)
        self.setLayout(layout)

        # اینستاگرام کلاینت
        self.client = None
        self.logged_in = False
        self.auto_like_comment_enabled = False

        # تایمر بررسی کامنت‌ها و لایک‌ها (هر 5 دقیقه)
        self.timer = QTimer()
        self.timer.timeout.connect(self.perform_scheduled_tasks)

        # شمارش فعالیت روزانه
        self.activity_count = 0

    def log(self, message):
        """نمایش پیام در لاگ"""
        self.log_text.append(message)
        print(message)

    def login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()

        if not username or not password:
            QMessageBox.warning(self, "هشدار", "نام کاربری و رمز عبور را وارد کنید.")
            return

        try:
            self.client = Client()
            self.client.login(username, password)
            self.logged_in = True
            self.log(f"✅ ورود موفق: {username}")

            # فعال کردن دکمه‌ها و تایمر
            self.login_button.setEnabled(False)
            self.logout_button.setEnabled(True)
            self.activity_count = 0
            self.timer.start(5 * 60 * 1000)  # هر 5 دقیقه

        except Exception as e:
            self.log(f"❌ خطا در ورود: {e}")
            QMessageBox.critical(self, "خطا", f"خطا در ورود: {e}")

    def logout(self):
        if self.client and self.logged_in:
            try:
                self.client.logout()
            except Exception:
                pass
        self.client = None
        self.logged_in = False
        self.auto_like_comment_enabled = False
        self.timer.stop()
        self.activity_count = 0

        self.login_button.setEnabled(True)
        self.logout_button.setEnabled(False)
        self.like_comment_button.setText("فعال کردن لایک و کامنت خودکار")

        self.log("⏹️ از حساب خارج شدید.")

    def get_config(self):
        try:
            limit = int(self.limit_input.text())
        except:
            limit = 10
        replies = [line.strip() for line in self.replies_input.toPlainText().split("\n") if line.strip()]
        hashtags = [line.strip() for line in self.hashtags_input.toPlainText().split("\n") if line.strip()]
        comment_text = self.comment_input.text().strip()
        trigger_comment = self.trigger_comment_input.text().strip()
        follow_reply = self.follow_reply_input.text().strip()
        success_reply = self.success_reply_input.text().strip()
        return {
            "daily_limit": limit,
            "replies": replies,
            "hashtags": hashtags,
            "comment_text": comment_text,
            "trigger_comment": trigger_comment,
            "follow_reply": follow_reply,
            "success_reply": success_reply
        }

    def toggle_auto_like_comment(self):
        if not self.logged_in:
            QMessageBox.warning(self, "هشدار", "ابتدا وارد حساب شوید.")
            return

        if not self.auto_like_comment_enabled:
            self.auto_like_comment_enabled = True
            self.like_comment_button.setText("غیرفعال کردن لایک و کامنت خودکار")
            self.log("🟢 لایک و کامنت خودکار فعال شد.")
        else:
            self.auto_like_comment_enabled = False
            self.like_comment_button.setText("فعال کردن لایک و کامنت خودکار")
            self.log("🔴 لایک و کامنت خودکار غیرفعال شد.")

    def perform_scheduled_tasks(self):
        if not self.auto_like_comment_enabled:
            return
        if not self.logged_in:
            self.log("❌ ربات متوقف شده است. لطفا دوباره وارد شوید.")
            return

        config = self.get_config()

        try:
            user_id = self.client.user_id_from_username(self.client.username)
        except Exception as e:
            self.log(f"❌ خطا در دریافت user_id: {e}")
            return

        # بررسی کامنت‌ها برای پاسخ به کامنت فعال‌کننده
        self.check_comments_and_reply(user_id, config)

        # لایک و کامنت روی پست‌های هشتگ‌ها
        self.like_and_comment_by_hashtags(config)

    def check_comments_and_reply(self, user_id, config):
        try:
            medias = self.client.user_medias(user_id, 10)
        except Exception as e:
            self.log(f"❌ خطا در دریافت پست‌ها: {e}")
            return

        try:
            followers = self.client.user_followers(user_id)
        except Exception as e:
            self.log(f"❌ خطا در دریافت فالوورها: {e}")
            followers = {}

        for media in medias:
            try:
                comments = self.client.media_comments(media.id)
            except Exception as e:
                self.log(f"❌ خطا در دریافت کامنت‌های پست {media.id}: {e}")
                continue

            for comment in comments:
                try:
                    if config["trigger_comment"] == "":
                        continue
                    if config["trigger_comment"] in comment.text:
                        commenter_id = comment.user.pk
                        if self.activity_count >= config["daily_limit"]:
                            self.log("⚠️ محدودیت تعداد پیام‌های روزانه رسید.")
                            return
                        if commenter_id not in followers:
                            # پیام درخواست فالو
                            try:
                                self.client.direct_send(config["follow_reply"], [commenter_id])
                                self.log(f"📩 ارسال پیام درخواست فالو به {comment.user.username}")
                                self.activity_count += 1
                            except Exception as e:
                                self.log(f"❌ خطا در ارسال پیام درخواست فالو: {e}")
                        else:
                            # پیام پاسخ اصلی
                            try:
                                self.client.direct_send(config["success_reply"], [commenter_id])
                                self.log(f"✅ ارسال پاسخ اصلی به {comment.user.username}")
                                self.activity_count += 1
                            except Exception as e:
                                self.log(f"❌ خطا در ارسال پاسخ اصلی: {e}")
                except Exception as e:
                    self.log(f"❌ خطا در پردازش کامنت‌ها: {e}")

    def like_and_comment_by_hashtags(self, config):
        for tag in config["hashtags"]:
            if self.activity_count >= config["daily_limit"]:
                self.log("⚠️ محدودیت تعداد فعالیت روزانه رسید.")
                return
            try:
                medias = self.client.hashtag_medias_recent(tag, amount=5)
            except Exception as e:
                self.log(f"❌ خطا در دریافت پست‌های هشتگ {tag}: {e}")
                continue

            for media in medias:
                if self.activity_count >= config["daily_limit"]:
                    self.log("⚠️ محدودیت تعداد فعالیت روزانه رسید.")
                    return

                try:
                    # لایک کردن
                    self.client.media_like(media.id)
                    self.log(f"❤️ لایک پست {media.id} از هشتگ #{tag}")
                    self.activity_count += 1

                    # کامنت گذاشتن
                    if config["comment_text"]:
                        self.client.media_comment(media.id, config["comment_text"])
                        self.log(f"💬 کامنت گذاشتن روی پست {media.id}: {config['comment_text']}")
                        self.activity_count += 1

                    # بین دو فعالیت کمی وقفه برای جلوگیری از بلاک
                    time.sleep(5)
                except ClientError as ce:
                    self.log(f"❌ خطای اینستاگرام: {ce}")
                except Exception as e:
                    self.log(f"❌ خطا در لایک/کامنت: {e}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = InstagramBotGUI()
    window.show()
    sys.exit(app.exec_())
