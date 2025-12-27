received = "Welcome to Our Enterprice"

def send_text(text):
    global received
    received = text

def to_online():
    return received
# dataset_parts = []

# for i in range(3):
#     item = reqd_dataset(i)
#     dataset_parts.append(item["chunk"])

# dataset = "\n".join(dataset_parts)
# print(dataset)

# def sent_llm():
#     return dataset