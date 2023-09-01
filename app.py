from worker import Worker  # Assuming your Worker class is in a separate module
from steam.guard import SteamAuthenticator
import json

def run_worker(OTP):
    worker = Worker("elianaastafqev", "kVscV10pQOcvO3EMdT", OTP)
    worker.run()

if __name__ == "__main__":
    with open("elianaastafqev.maFile", 'r') as file:
        file_contents = file.read()

    # Parse the file contents as JSON
    try:
        data = json.loads(file_contents)
    except json.JSONDecodeError as e:
        print("Error decoding JSON:", e)

    sa = SteamAuthenticator(data)
    run_worker(sa.get_code())

