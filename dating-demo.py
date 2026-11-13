class DialogueOption:
    text = ""
    effect = 0.0
    response = None

    def __init__(self, text, effect, response):
        self.text = text
        self.effect = effect
        self.response = response
        

class DialogueNode:
    text = ""
    options = []

    def __init__(self, text, options):
        self.text = text
        self.options = options
         


def init_date():
    responseA = DialogueNode("Wow, that's rude", [])
    responseB = DialogueNode("Wow, that's so funny", [])
    root = DialogueNode("Hello, i am date", [DialogueOption("fuck off", -5.0, responseA), DialogueOption("hello date, i am dad", 5.0, responseB)])
    return root



if __name__ == "__main__":
    date_excitement = 5.0
    tree = init_date()

    while True:

        print(tree.text)
        for i, option in enumerate(tree.options):
            print(f"{str(i + 1)}: " + option.text)
    
        choice = input()
        if choice not in map(str, range(len(tree.options))):
            print("invalid choice, try again")
            choice = input()
        choice = int(choice) - 1
            
        date_excitement += tree.options[choice].effect
        tree = tree.options[choice].response 

        if date_excitement <= 0.0:
            print("Date got bored and you lose")
            break
        if date_excitement >= 10.0:
            print("awooga")
            break

        if not tree.options:
            print("dialogue tree ends here")
            break
                                

