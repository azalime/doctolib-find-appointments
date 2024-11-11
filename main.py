from time import sleep
from playwright.sync_api import sync_playwright
from datetime import date, timedelta, datetime
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.app import App
from kivy.metrics import dp
from kivy.uix.scrollview import ScrollView
from nava import play, stop

# User Parameter __MUST BE CHANGED__
# For Cabinet Tour Mercure https://www.doctolib.fr/cabinet-medical/mantes-la-jolie/cabinet-medical-mantes-la-jolie
visit_motive_ids = "2363648"
agenda_ids = "375237-375239-375240-375244-375753" # 375237=badaoui, 375240=merfoud, 375237-375239-375240-375244-375753=all
practice_ids = "149047"
telehealth = "false"

# Optional User Parameters
days = 6
minutes = 2


class Doctolib(App):
    def __init__(self, available_days):
        super().__init__()
        self.available_days = available_days

    def build(self):
        # Create the content of the alert dialog
        scrollview = ScrollView()
        content = BoxLayout(orientation="vertical", size_hint_y=None, spacing=5)
        content.bind(minimum_height=content.setter("height"))

        for day, slots in self.available_days.items():
            label_text = f"Day: {day}:\nSlots:\n" + "\n".join([f"    {slot}" for slot in slots])
            label = Label(text=label_text, size_hint=(1, None), height=(len(slots) + 2) * dp(25))
            content.add_widget(label)

        scrollview.add_widget(content)

        # Create and open the alert dialog
        popup = Popup(title="Available Appointments", content=scrollview, size_hint=(None, None), size=(1000, 1000))
        popup.open()


def check_available_appointments(data):
    available_days = {}
    for availability in data["availabilities"]:
        cur_date = availability["date"]
        if start_date <= cur_date <= end_date:
            slots = availability["slots"]
            if slots:
                available_days[cur_date] = slots
    return available_days


while True:
    # System parameters
    limit = "15"
    start_date = date.today().strftime("%Y-%m-%d")
    end_date = (date.today() + timedelta(days=days)).strftime("%Y-%m-%d")
    url = (
        f"https://www.doctolib.de/availabilities.json?"
        f"visit_motive_ids={visit_motive_ids}&"
        f"agenda_ids={agenda_ids}&"
        f"practice_ids={practice_ids}&"
        f"telehealth={telehealth}&"
        f"limit={limit}&"
        f"start_date={start_date}&"
        f"end_date={end_date}"
    )

    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            " (KHTML, like Gecko) Chrome/89.0.4389.114 Safari/537.36"
        )
        page = context.new_page()
        response = page.goto(url)
        data = response.json()

        # Check for available appointments
        available_days = check_available_appointments(data)
        if available_days:
            # Play alarm
            sound_id = play("alarm.wav", async_mode=True)
            sleep(4)
            stop(sound_id)
            print('Go https://www.doctolib.fr/cabinet-medical/mantes-la-jolie/cabinet-medical-mantes-la-jolie/booking/practitioners?specialityId=2&telehealth=false&placeId=practice-149047&isNewPatient=false&isNewPatientBlocked=false&motiveIds%5B%5D=2363648&bookingFunnelSource=profile')
            Doctolib(available_days).run()
            exit(0)
        time_now = datetime.now().strftime("%H:%M:%S")
        print(f"At {time_now} : no available appointments found in the next {days} day(s)")
    sleep(60 * minutes)
