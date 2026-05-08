import requests
import re

system_prompt = """

You are a structured data extraction system.

Your task is to generate a valid JSON object representing a qualitative codebook based on an input text (e.g. interview transcript or other content).

You MUST follow these rules strictly:

1. Output ONLY valid JSON. No explanations, no comments, no extra text before or after.
2. The JSON must be syntactically correct and parsable.
3. Use double quotes for all keys and string values.
4. Do not include trailing commas.
5. Do not include undefined or null fields. Always fill fields with meaningful content.
6. Keep all text in the same language as the input.

### JSON Structure

The output must follow exactly this schema:

{
  "codebook": [
    {
      "code": "string",
      "definition": "string",
      "example": "string",
      "notes": "string",
      "subcodes": [
        {
          "code": "string",
          "definition": "string",
          "example": "string",
          "notes": "string"
        }
      ]
    }
  ]
}

### Coding Guidelines

- Identify meaningful themes, concepts, or categories in the text.
- Create clear, concise, and descriptive code names.
- Group related codes under a parent code using "subcodes".
- Only create "subcodes" if there is a clear hierarchical relationship.
- Avoid duplication.
- Keep definitions precise and analytical, not vague.
- Use short excerpts from the text as examples.
- "notes" can include context, ambiguity, or coding guidance.

### Output Constraints

- Minimum 5 codes.
- Maximum 15 codes.
- Each code should have at least 1 meaningful sentence in "definition".
- Use subcodes where appropriate, but do not force them.

Remember:
Output ONLY the JSON object. Nothing else.
If the output is not in the input language translate it.
"""

user_prompt = """

So, fast. Ja, also im Endeffekt, also ich bin Masterstudent in Graz an der TH-Fakultät und jetzt bald am fertig werden und wir haben das Projektseminar, das ist immer ein Seminar, in dem wir sozusagen ein Forschungsprojekt machen müssen, um
hilflich sein soll, Daten zu verarbeiten, leichter zu verarbeiten, zugänglich zu machen und da bin ich jetzt eben derzeit noch in der Use-Case-Analyse sozusagen, das heißt, ich mache jetzt eben mit dir und einem und zwei anderen nur Interviews dazu, inwiefern man so ein Tool circa für die jeweiligen Projekte nutzen könnte.
Das wäre jetzt bei dir eben auf das ManMax bezogen, da war jetzt nicht sicher, das war eben der Georg auch nicht sicher, inwiefern du da mit den Daten direkt arbeitest, also mit den Hintergrunddaten sozusagen.
Wie viel quasi weißt du vom Projekt, also was kann ich quasi voraussetzen an Wissen?
Also ich habe diesen JSON-Datensatz von Herrn Heiden bekommen, den habe ich mir ein bisschen durchgeschaut und ich habe mir sozusagen die Website vom Projekt ein bisschen angeschaut, also das ist meine Basis.
Okay, verstehe. Also ich war jemand, der geholfen hat, diese Daten auch zu säubern, also er hat so von einer sehr veralteten Software, von einer älteren Dame bekommen,
diesen Grundstock, das Schuhregister, ich weiß nicht, ob da das versagt, und das war halt so Excel-Tabelle, weil sie so absolut, ihr Mann hat irgendeinen Flashplayer-Ding gemacht, damit sie leichter Buchregister schreiben kann damit.
Also so ist das Ganze entstanden. Und deswegen haben wir rübergehen müssen, weil das Programm, das der Herr Heiden eben verwendet hat,
er hat zum Beispiel Leute wie den Kaiser Maximilian als Ort getaggt, automatisch, weil er es nicht gescheit gekannt hat.
Deswegen war unsere erste Aufgabe, war das mal zu säubern und uns überhaupt die Frage zu stellen, bei manchen Sachen, also beim Kaiser war es natürlich leicht zu sagen,
okay, gut, das ist eine Person und kein Ort. Aber zum Beispiel, wenn es darum ging, was machst du mit einer Stadtgemeinde?
Weil das ist einerseits ein Ort und andererseits eine Personengruppe und dann eigentlich wieder auch eine Organisation.
Und das war für uns am Anfang total schwer, auch das, wir haben sehr viel gestritten untereinander, sagen wir es mal so,
weil manche Sachen waren halt nicht so leicht. Und jetzt arbeite ich ein bisschen weniger damit, weil ich schreibe Registen und ich tagge nur die Personen, Orte, Organisationen, die da vorkommen.
Und das ist quasi momentan mein Beitrag zur Datenbank. Also momentan ist recht wenig. Am Anfang war ich sehr viel beteiligt damit, ja.
Okay. Und mir ist jetzt auch noch die Frage aufgekommen, eben, habt ihr dieses Factor jetzt Chasen bekommen, was spielt das im Projekt für eine Rolle sozusagen?
Ist das sozusagen der Grunddatensatz von dem Projekt?
Ja, das ist quasi, soll auch das große Ergebnis dann sein, dass wir quasi die tollste, beste Datenbank in global haben zum Maximilian.
Das ist der Anspruch, den wir in unseren Projektleiter gesetzt haben, ja.
Okay, und wird da jetzt schon irgendwie interagiert mit den Daten derzeit? Oder ist das nur im Aufbau sozusagen?
Beides. Also das Problem ist, wir haben halt diesen Grundstock, den man gekriegt hat, eben dieses Schuhregister.
Ja.
Und nebenbei soll man halt parallel auch natürlich in die Datenbank reinarbeiten.
Aber manche Kollegen von uns haben halt jetzt schon sehr viel reingearbeitet, zum Beispiel für ihre speziellen Interessen.
Ja.
Und die haben sich das auch schon rausgeholt von der, ich kann nur ihren Vornamen, von der Marcella, ich weiß nicht, ob du die schon mal gesehen hast.
Sie unterrichtet jetzt auch in Graz.
Die macht viel Netzwerkanalyse.
Mhm.
Und die hat halt geholfen.


"""

headers = {
    'Content-Type': 'application/json',
}

json_data = {
    'model': 'Qwen/Qwen3-14B-AWQ',
    'messages': [
        {
            'role': 'system',
            'content': f'{system_prompt}',
        },
        {
            'role': 'user',
            'content': f'{user_prompt}',
        },
    ],
}

response = requests.post('http://localhost:8000/v1/chat/completions', headers=headers, json=json_data)

print(response.text)

data = response.json()
content = data["choices"][0]["message"]["content"]

content = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL).strip()
print(content)

#data = json.loads(response)
