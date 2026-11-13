class DialogueOption:
    text = ""
    effect = 0.0
    response = None
    requrement = ""

    def __init__(self, text, effect, response, requirement=None):
        self.text = text
        self.effect = effect
        self.response = response
        if requirement: self.requrement = requirement
        

class DialogueNode:
    text = ""
    options = []

    def __init__(self, text, options):
        self.text = text
        self.options = options
     

def init_date():
    responseA = DialogueNode("Wow, that's rude", [])
    responseB = DialogueNode("Wow, that's so funny", [])
    responseC = DialogueNode("Wow that's interessting", [])
    root = DialogueNode("Hello, i am date", [DialogueOption("fuck off", -5.0, responseA), DialogueOption("hello date, i am dad", 5.0, responseB), DialogueOption("Did you know <interessting fact>", 5.0, responseC, "interessting_fact_skill")])
    return root



if __name__ == "__main__":
    date_excitement = 5.0
    tree = init_date()
    skills = ["interessting_fact_skill"]

    print(tree.text)
    while True:
        unavailable = []
        for i, option in enumerate(tree.options):
            if (option.requrement and option.requrement not in skills):
                print(f"{str(i + 1)}: Hidden option")
                unavailable += [i + 1]
            else:
                print(f"{str(i + 1)}: " + option.text)
    
        choice = input()
        if choice not in map(str, range(1, len(tree.options) + 1)) or int(choice) in unavailable:
            print("invalid choice, try again")
            choice = input()
        choice = int(choice) - 1
            
        date_excitement += tree.options[choice].effect
        tree = tree.options[choice].response 
        print(tree.text)

        if date_excitement <= 0.0:
            print("Date got bored and you lose")
            break

        if date_excitement >= 10.0:
            print("you win date, awooga")
            break

        if not tree.options:
            print("dialogue tree ends here")
            break
                                

