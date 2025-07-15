# app.py
from workflows.main_graph import main_workflow

if __name__ == "__main__":
    #topic = input("Enter the topic for your article: ")
    topic = "Fujifilm X100V"
    article = main_workflow(topic)
    print("\nGenerated Article:\n")
    print(article)
