import requests

print("🟢 Sending topic to the writer agent...")
topic = {"topic": "Future of AI in Education"}
res1 = requests.post("http://localhost:8000/write", json=topic)
data1 = res1.json()

if "text" not in data1:
    print("❌ Error from writer agent:", data1.get("error"))
    exit()

print("✅ Text received:\n", data1["text"])

print("\n🟢 Sending text to the critic agent...")
res2 = requests.post("http://localhost:8001/critique", json={"text": data1["text"]})
data2 = res2.json()

if "feedback" not in data2:
    print("❌ Error from critic agent:", data2.get("error"))
else:
    print("✅ Feedback received:\n", data2["feedback"])