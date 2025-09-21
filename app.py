from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import google.generativeai as genai
import os
from dotenv import load_dotenv
import requests
import random
from datetime import datetime
import json
from typing import List, Optional
from fastapi.middleware.cors import CORSMiddleware

# Load environment variables
load_dotenv()

# Configure Gemini API
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
model = None
if GOOGLE_API_KEY:
    try:
        genai.configure(api_key=GOOGLE_API_KEY)
        # ✅ Use free Gemini 1.5 Flash model instead of gemini-pro
        model = genai.GenerativeModel('gemini-1.5-flash')
        print("✅ Google Gemini 1.5 Flash API configured successfully!")
    except Exception as e:
        print(f"Error configuring Gemini: {e}")
        model = None
else:
    print("⚠️  GOOGLE_API_KEY not found. Running with limited AI capabilities.")

# FastAPI app initialization
app = FastAPI(title="Sakha.ai", description="Comprehensive Mental Health & Wellness Companion")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for request/response
class ChatMessage(BaseModel):
    message: str
    mode: str = "normal"  # "normal", "gita", "inspire"
    language: str = "en"  # Language preference

class ChatResponse(BaseModel):
    response: str
    mood: str
    crisis_detected: bool
    timestamp: str
    mode: str
    language: str

class WisdomContent(BaseModel):
    type: str  # "gita", "leadership", "epic"
    content: dict

class SakhaAI:
    def __init__(self):
        self.conversation_history = []
        
        # Enhanced Bhagavad Gita wisdom database
        self.gita_quotes =  [
  {
    "shloka": "धृतराष्ट्र उवाच । धर्मक्षेत्रे कुरुक्षेत्रे समवेता युयुत्सवः । मामकाः पाण्डवाश्चैव किमकुर्वत सञ्जय ॥",
    "translation": "Dhritarashtra said: O Sanjaya, assembled in the holy land of Kurukshetra and desiring to fight, what did my sons and the sons of Pandu do?",
    "chapter": "Chapter 1, Verse 1",
    "context": "Dhritarashtra asks Sanjaya about the battlefield of Kurukshetra.",
    "practical_meaning": "Conflict begins due to attachment and blindness (literal and symbolic).",
    "life_application": "When facing conflicts, try to see clearly instead of being blinded by attachment.",
    "keywords": ["conflict", "blindness", "attachment", "battle", "Kurukshetra"]
  },
  {
    "shloka": "सञ्जय उवाच । दृष्ट्वा तु पाण्डवानीकं व्यूढं दुर्योधनस्तदा । आचार्यमुपसङ्गम्य राजा वचनमब्रवीत् ॥",
    "translation": "Sanjaya said: O King, after observing the Pandava army arranged in military formation, King Duryodhana approached his teacher Drona and spoke the following words.",
    "chapter": "Chapter 1, Verse 2",
    "context": "Duryodhana goes to Drona and describes the enemy’s formation.",
    "practical_meaning": "Even the arrogant seek guidance when faced with challenges.",
    "life_application": "Seek advice when in tough situations, but remain aware of your intentions.",
    "keywords": ["guidance", "challenge", "arrogance", "battle"]
  },
  {
    "shloka": "पश्यैतां पाण्डुपुत्राणामाचार्य महतीं चमूम् । व्यूढां द्रुपदपुत्रेण तव शिष्येण धीमता ॥",
    "translation": "Behold, O teacher, the mighty army of the sons of Pandu, arranged in military formation by the son of Drupada, your wise disciple.",
    "chapter": "Chapter 1, Verse 3",
    "context": "Duryodhana points out that Drona’s own disciple is leading the Pandava army.",
    "practical_meaning": "Life’s irony — one’s own student can oppose the teacher.",
    "life_application": "Don’t underestimate others, even if they once learned from you.",
    "keywords": ["teacher", "student", "battle", "irony"]
  },
  {
    "shloka": "अत्र शूरा महेष्वासा भीमार्जुनसमा युधि । युयुधानो विराटश्च द्रुपदश्च महारथः ॥",
    "translation": "Here in this army are many heroic bowmen equal in fighting to Bhima and Arjuna; great fighters like Yuyudhana, Virata, and Drupada.",
    "chapter": "Chapter 1, Verse 4",
    "context": "Duryodhana lists the warriors in Pandava’s army.",
    "practical_meaning": "Recognizing the strength of the opposition is necessary before battle.",
    "life_application": "Know the strength of challenges before facing them.",
    "keywords": ["warriors", "strength", "opposition", "battle"]
  },
  {
    "shloka": "धृष्टकेतुश्चेकितानः काशिराजश्च वीर्यवान् । पुरुजित्कुन्तिभोजश्च शैब्यश्च नरपुङ्गवः ॥",
    "translation": "There are also great, heroic men like Dhrishtaketu, Chekitana, the valiant king of Kasi, Purujit, Kuntibhoja, and Shaibya, the best of men.",
    "chapter": "Chapter 1, Verse 5",
    "context": "Duryodhana continues naming strong warriors in Pandava’s army.",
    "practical_meaning": "Acknowledging the qualities of opponents shows awareness of the challenge.",
    "life_application": "Be aware of all forces at play in any situation.",
    "keywords": ["heroes", "awareness", "battle", "opposition"]
  },
  {
    "shloka": "युधामन्युश्च विक्रान्त उत्तमौजाश्च वीर्यवान् । सौभद्रो द्रौपदेयाश्च सर्व एव महारथाः ॥",
    "translation": "There are the heroic Yudhamanyu, the valiant Uttamauja, Abhimanyu, the son of Subhadra, and the five sons of Draupadi—all great chariot-warriors.",
    "chapter": "Chapter 1, Verse 6",
    "context": "Duryodhana emphasizes the strength of Pandava warriors.",
    "practical_meaning": "Acknowledges younger but powerful fighters like Abhimanyu.",
    "life_application": "Even youth can show great strength when inspired by purpose.",
    "keywords": ["youth", "strength", "courage", "battle"]
  },
  {
    "shloka": "अस्माकं तु विशिष्टा ये तान्निबोध द्विजोत्तम । नायका मम सैन्यस्य संज्ञार्थं तान्ब्रवीमि ते ॥",
    "translation": "But for your information, O best of the Brahmanas, let me tell you about the leaders of my own army, who are most distinguished.",
    "chapter": "Chapter 1, Verse 7",
    "context": "Duryodhana shifts focus to his own army’s leaders.",
    "practical_meaning": "Confidence arises when recognizing strengths on one’s side.",
    "life_application": "Acknowledge your own strengths before facing challenges.",
    "keywords": ["leaders", "strength", "confidence"]
  },
  {
    "shloka": "भवान्भीष्मश्च कर्णश्च कृपश्च समितिञ्जयः । अश्वत्थामा विकर्णश्च सौमदत्तिस्तथैव च ॥",
    "translation": "There are personalities like yourself, Bhishma, Karna, Kripa—conquerors in battle; Ashwatthama, Vikarna, and Bhurishrava, son of Somadatta.",
    "chapter": "Chapter 1, Verse 8",
    "context": "Duryodhana names his own side’s great warriors.",
    "practical_meaning": "Confidence builds by recalling the heroes on one’s side.",
    "life_application": "Remember your support system when facing challenges.",
    "keywords": ["support", "confidence", "heroes"]
  },
  {
    "shloka": "अन्ये च बहवः शूरा मदर्थे त्यक्तजीविताः । नानाशस्त्रप्रहरणाः सर्वे युद्धविशारदाः ॥",
    "translation": "There are also many other heroes who are prepared to lay down their lives for my sake. All of them are well equipped with weapons and experienced in military science.",
    "chapter": "Chapter 1, Verse 9",
    "context": "Duryodhana mentions other loyal warriors.",
    "practical_meaning": "A strong team is not only about leaders but also about loyal followers.",
    "life_application": "Value the dedication of those who stand with you.",
    "keywords": ["loyalty", "team", "dedication", "support"]
  },
  {
    "shloka": "अपर्याप्तं तदस्माकं बलं भीष्माभिरक्षितम् । पर्याप्तं त्विदमेतेषां बलं भीमाभिरक्षितम् ॥",
    "translation": "Our strength, protected by Bhishma, is unlimited, whereas the strength of the Pandavas, carefully protected by Bhima, is limited.",
    "chapter": "Chapter 1, Verse 10",
    "context": "Duryodhana compares his army with that of Pandavas.",
    "practical_meaning": "Perception of strength often depends on who is leading.",
    "life_application": "Your confidence grows when guided by strong mentors.",
    "keywords": ["strength", "perception", "leader", "confidence"]
  },
  {
    "shloka": "ततः शङ्खाश्च भेर्यश्च पणवानकगोमुखाः। स शुक्रसहस्रेषु ध्वनन्त्यथाब्रवीत् युधि॥",
    "translation": "Then, the conchs, drums, bugles, trumpets, and horns were all suddenly sounded, making a tremendous noise.",
    "chapter": "Chapter 1, Verse 11",
    "context": "The battle preparations begin with the sounding of instruments.",
    "practical_meaning": "Signifies the commencement of action after preparation.",
    "life_application": "When starting a big task, ensure proper preparation and signal readiness.",
    "keywords": ["battle", "preparation", "announcement", "action"]
  },
  {
    "shloka": "ततः श्वेतैर्हयैर्युक्ते महति स्यन्दने स्थितौ। माधवः पाण्डवश्चैव दिव्यौ शङ्खौ प्रदध्मतुः॥",
    "translation": "Then Krishna and Arjuna, stationed in the great chariot yoked with white horses, blew their divine conches.",
    "chapter": "Chapter 1, Verse 12",
    "context": "Krishna and Arjuna signal readiness to begin the battle.",
    "practical_meaning": "Even the leader must lead by example.",
    "life_application": "Show readiness and courage when starting important tasks.",
    "keywords": ["leadership", "example", "courage", "preparation"]
  },
  {
    "shloka": "पञ्चजन्यं हृषीकेशो देवदत्तं धनञ्जयः। पाञ्चजन्यं शुभं चक्रे भीष्मादिभिरक्षितम्॥",
    "translation": "Krishna blew the Panchajanya conch, Arjuna blew the Devadatta conch, and the conches of the warriors protected by Bhishma sounded.",
    "chapter": "Chapter 1, Verse 13",
    "context": "The conches of both sides announce the battle.",
    "practical_meaning": "Coordination and unity amplify the impact.",
    "life_application": "Team coordination is essential before any major action.",
    "keywords": ["coordination", "teamwork", "announcement", "unity"]
  },
  {
    "shloka": "ततः शङ्खाश्च भेर्यश्च पणवानकगोमुखाः। धृष्टद्युम्नेन धृष्टकृष्णेन च प्रदध्मतुः॥",
    "translation": "Then Dhrishtadyumna, Dhrishtaketu, and the other warriors blew their respective conches.",
    "chapter": "Chapter 1, Verse 14",
    "context": "All leaders signal readiness with their own instruments.",
    "practical_meaning": "Every role contributes to the collective effort.",
    "life_application": "In a team, everyone’s contribution counts toward success.",
    "keywords": ["leadership", "roles", "teamwork", "coordination"]
  },
  {
    "shloka": "सञ्जय उवाच । एवमुक्त्वा हृषीकेशं गुडाकेशः प्रणम्य। एवमुक्त्वा हृषीकेशं प्रणम्य पाण्डवर्षभः॥",
    "translation": "Sanjaya said: Having spoken thus, Gudakesha (Arjuna) bowed down to Krishna.",
    "chapter": "Chapter 1, Verse 15",
    "context": "Arjuna shows respect and humility to his charioteer and guide.",
    "practical_meaning": "Even the strongest warrior shows respect to guidance.",
    "life_application": "Respect mentors and guides; humility strengthens action.",
    "keywords": ["humility", "respect", "guidance", "mentor"]
  },
  {
    "shloka": "अर्जुन उवाच । सेनयोरुभयोर्मध्ये रथं स्थापय मेऽच्युत। याचितोऽस्मि युद्धाय सम्भवं हि न संशयः॥",
    "translation": "Arjuna said: Place my chariot in the midst of the two armies, O Achyuta (Krishna). I am eager to see those assembled for battle.",
    "chapter": "Chapter 1, Verse 16",
    "context": "Arjuna requests to see both sides clearly before the battle begins.",
    "practical_meaning": "One must assess a situation before acting.",
    "life_application": "Evaluate challenges before diving into action.",
    "keywords": ["assessment", "preparation", "observation", "clarity"]
  },
  {
    "shloka": "सञ्जय उवाच । ततो युद्धे प्रियसखः शंकरप्रसादकः। तस्य रथं स्थापयामास सत्तामुल्लङ्घ्य युधि॥",
    "translation": "Sanjaya said: Then Krishna placed Arjuna’s chariot in the midst of the armies, ready to fight.",
    "chapter": "Chapter 1, Verse 17",
    "context": "Krishna positions Arjuna at the center of the battlefield.",
    "practical_meaning": "A leader provides stability and support in the center of challenges.",
    "life_application": "Strong support at critical points ensures success.",
    "keywords": ["support", "leadership", "battle", "positioning"]
  },
  {
    "shloka": "अर्जुन उवाच । सञ्जय ! दृष्ट्वा हृषीकेशं सेना ममाः। मनः क्लान्तम्, वचनात् मोहितम्, किमिदानीं युधि॥",
    "translation": "Arjuna said: O Sanjaya, seeing my own kinsmen arrayed in battle, my mind is confused and my strength fails.",
    "chapter": "Chapter 1, Verse 18",
    "context": "Arjuna begins to feel moral doubt and sorrow at the thought of killing relatives.",
    "practical_meaning": "Conflicting duties can create mental stress.",
    "life_application": "Facing moral dilemmas requires reflection and calm judgment.",
    "keywords": ["conflict", "stress", "morality", "doubt"]
  },
  {
    "shloka": "कुतस्त्वा कश्मलमिदं विषमे समुपस्थितम्। अनार्यजुष्टमस्वर्ग्यमकीर्तिकरमर्जुन॥",
    "translation": "Arjuna said: O Keshava (Krishna), why is this faint-heartedness coming upon me at the battlefield? It is not proper for a noble person.",
    "chapter": "Chapter 1, Verse 19",
    "context": "Arjuna expresses his confusion and fear about fighting.",
    "practical_meaning": "Even the strong can face fear in extreme situations.",
    "life_application": "Acknowledge fear but analyze it rationally before acting.",
    "keywords": ["fear", "doubt", "confusion", "noble"]
  },
  {
    "shloka": "न च श्रेयोऽनुपश्यामि हत्वा स्वजनमाहवे। यद्यपि प्रतिष्ठां स्थापयेमि स्वल्पमप्ययुधि॥",
    "translation": "Arjuna said: I cannot see any good in killing my own relatives in battle, even for the kingdom or pleasures.",
    "chapter": "Chapter 1, Verse 20",
    "context": "Arjuna refuses to fight against his family and teachers.",
    "practical_meaning": "Violence against loved ones brings moral anguish.",
    "life_application": "Avoid actions that violate your conscience, even for worldly gain.",
    "keywords": ["moral", "conscience", "dilemma", "family"]
  },
  {
    "shloka": "सञ्जय उवाच । एवमुक्तो हृषीकेशं प्राह लक्ष्मणसमाभवः।",
    "translation": "Sanjaya said: Arjuna spoke thus, and his mind became overwhelmed with sorrow.",
    "chapter": "Chapter 1, Verse 21",
    "context": "Arjuna is confused and despondent at the prospect of fighting his relatives.",
    "practical_meaning": "Even the bravest can be paralyzed by moral dilemmas.",
    "life_application": "Pause and reflect when faced with difficult moral choices.",
    "keywords": ["sorrow", "moral dilemma", "confusion", "despondency"]
  },
  {
    "shloka": "न ही प्रपश्यामि मम जन्मभूमौ परिवार्यं।",
    "translation": "I see no benefit in killing my own kinsmen on this battlefield.",
    "chapter": "Chapter 1, Verse 22",
    "context": "Arjuna laments the potential destruction of his family.",
    "practical_meaning": "Recognize the consequences of your actions.",
    "life_application": "Think through long-term effects before taking drastic actions.",
    "keywords": ["consequences", "family", "reflection", "duty"]
  },
  {
    "shloka": "न च हि प्रपश्यामि धर्मस्य हानिमाप्नुयाम।",
    "translation": "I cannot see any righteousness in slaying my relatives.",
    "chapter": "Chapter 1, Verse 23",
    "context": "Arjuna questions the righteousness of war against his kin.",
    "practical_meaning": "Actions contrary to dharma create inner conflict.",
    "life_application": "Avoid actions that violate ethical or moral principles.",
    "keywords": ["righteousness", "ethics", "conflict", "dharma"]
  },
  {
    "shloka": "कुलनाशाय कुतः सुखं? अनर्थेषु हि सुखम्।",
    "translation": "How can there be happiness in the destruction of family? True happiness is impossible in such misfortune.",
    "chapter": "Chapter 1, Verse 24",
    "context": "Arjuna realizes the sorrow that family destruction brings.",
    "practical_meaning": "True happiness cannot come from harming others.",
    "life_application": "Seek actions that create benefit, not harm, for others.",
    "keywords": ["happiness", "misfortune", "family", "ethics"]
  },
  {
    "shloka": "सञ्जय उवाच । अर्जुन शोकान्वितः स्थावरमिव सङ्ग्रामे।",
    "translation": "Sanjaya said: Arjuna, filled with grief, sat down in the chariot, overwhelmed like one immobilized.",
    "chapter": "Chapter 1, Verse 25",
    "context": "Arjuna’s grief renders him inactive, like a statue.",
    "practical_meaning": "Emotional overwhelm can paralyze action.",
    "life_application": "Recognize emotional blocks and seek clarity before acting.",
    "keywords": ["grief", "paralysis", "emotion", "overwhelm"]
  },
  {
    "shloka": "मम मनः क्लान्तं, नास्ति चेतसा विहारम्।",
    "translation": "My mind is weary; it has no vigor to act.",
    "chapter": "Chapter 1, Verse 26",
    "context": "Arjuna expresses mental exhaustion and loss of resolve.",
    "practical_meaning": "Mental fatigue can impede decision-making.",
    "life_application": "Rest, reflect, and regain mental clarity before tackling challenges.",
    "keywords": ["mental fatigue", "decision-making", "reflection", "clarity"]
  },
  {
    "shloka": "सञ्जय उवाच । अर्जुन दृष्ट्वा तु पाण्डवानीकं सन्नद्धम्।",
    "translation": "Sanjaya said: Seeing the Pandava army fully prepared, Arjuna felt compassion and sorrow.",
    "chapter": "Chapter 1, Verse 27",
    "context": "Arjuna is struck by empathy for those he must fight.",
    "practical_meaning": "Empathy can create moral tension in duty-bound situations.",
    "life_application": "Balance duty with compassion to make ethical decisions.",
    "keywords": ["empathy", "duty", "moral tension", "compassion"]
  },
  {
    "shloka": "किं करिष्ये? यदा धर्मो हानिर्भवति।",
    "translation": "What should I do when performing my duty brings harm?",
    "chapter": "Chapter 1, Verse 28",
    "context": "Arjuna questions the moral justification of his actions.",
    "practical_meaning": "Conflict arises when duty seems to contradict morality.",
    "life_application": "Seek guidance and wisdom when facing conflicting responsibilities.",
    "keywords": ["conflict", "duty", "morality", "guidance"]
  },
  {
    "shloka": "न हि प्रपश्यामि सुखं हत्वा स्वजनमाहवे।",
    "translation": "I cannot see any happiness in killing my own family, even for pleasure or kingdom.",
    "chapter": "Chapter 1, Verse 29",
    "context": "Arjuna reiterates his refusal to fight against loved ones.",
    "practical_meaning": "Harming loved ones is inherently unsatisfactory.",
    "life_application": "Avoid decisions that bring harm to those you care about.",
    "keywords": ["family", "harm", "reflection", "ethics"]
  },
  {
    "shloka": "कुलधर्मं न हि शोभते हत्वा स्वजनमाहवे।",
    "translation": "It is not appropriate to destroy family duty by harming one’s own kin.",
    "chapter": "Chapter 1, Verse 30",
    "context": "Arjuna emphasizes the importance of dharma and family duty.",
    "practical_meaning": "Family duty and ethical action are inseparable.",
    "life_application": "Always consider ethical principles before acting, especially toward loved ones.",
    "keywords": ["dharma", "family", "ethics", "duty"]
  },
  {
    "shloka": "सञ्जय उवाच । अर्जुनोऽपि न शोभते हत्वा स्वजनमाहवे।",
    "translation": "Sanjaya said: Arjuna also saw that killing his own relatives was not proper.",
    "chapter": "Chapter 1, Verse 31",
    "context": "Arjuna recognizes the immorality of harming his own family.",
    "practical_meaning": "Even the bravest can recognize when an action is ethically wrong.",
    "life_application": "Pause and consider ethics before taking major actions.",
    "keywords": ["ethics", "family", "immorality", "reflection"]
  },
  {
    "shloka": "सञ्जय उवाच । तस्य शोकाभिभूतस्य क्लान्तमनसस्य च।",
    "translation": "Sanjaya said: His mind was overwhelmed with grief and exhaustion.",
    "chapter": "Chapter 1, Verse 32",
    "context": "Arjuna’s grief makes him mentally exhausted and indecisive.",
    "practical_meaning": "Emotional overwhelm can impair judgment.",
    "life_application": "Take a step back to regain mental clarity before acting.",
    "keywords": ["grief", "exhaustion", "mental clarity", "decision-making"]
  },
  {
    "shloka": "न हि श्रेयः हत्वा स्वजनमाहवे।",
    "translation": "There is no gain in killing one’s own kin.",
    "chapter": "Chapter 1, Verse 33",
    "context": "Arjuna questions the purpose of the war against family members.",
    "practical_meaning": "Destruction of loved ones has no real benefit.",
    "life_application": "Evaluate actions for true benefit rather than immediate gain.",
    "keywords": ["gain", "family", "reflection", "benefit"]
  },
  {
    "shloka": "कुलनाशाय कुतः सुखं? अनर्थेषु हि सुखम्।",
    "translation": "How can there be happiness in the destruction of family? True happiness cannot come from misfortune.",
    "chapter": "Chapter 1, Verse 34",
    "context": "Arjuna reflects on the misery caused by family destruction.",
    "practical_meaning": "Harm to loved ones brings suffering, not happiness.",
    "life_application": "Avoid actions that create misery for others.",
    "keywords": ["happiness", "misfortune", "family", "reflection"]
  },
  {
    "shloka": "अहं कृत्स्नं पापं करोमि स्वजनमाहवे।",
    "translation": "I commit complete sin by attacking my own relatives.",
    "chapter": "Chapter 1, Verse 35",
    "context": "Arjuna realizes the sinful nature of fighting his family.",
    "practical_meaning": "Actions against moral law are considered sinful.",
    "life_application": "Be mindful of ethical consequences of your actions.",
    "keywords": ["sin", "ethics", "morality", "family"]
  },
  {
    "shloka": "सञ्जय उवाच । अर्जुनोऽपि शोकान्वितः रथे स्थिता।",
    "translation": "Sanjaya said: Arjuna, filled with sorrow, sat down on the chariot.",
    "chapter": "Chapter 1, Verse 36",
    "context": "Arjuna becomes immobile from grief and confusion.",
    "practical_meaning": "Grief can freeze a person into inaction.",
    "life_application": "Acknowledge grief but seek clarity before making decisions.",
    "keywords": ["grief", "inaction", "confusion", "reflection"]
  },
  {
    "shloka": "मम मनः क्लान्तं, न हि प्रहर्तुमिच्छामि।",
    "translation": "My mind is exhausted; I do not wish to fight.",
    "chapter": "Chapter 1, Verse 37",
    "context": "Arjuna expresses his unwillingness to continue the battle.",
    "practical_meaning": "Exhaustion can diminish motivation and resolve.",
    "life_application": "Rest and reflection help regain mental strength for action.",
    "keywords": ["exhaustion", "motivation", "resolve", "mental clarity"]
  },
  {
    "shloka": "किं करिष्ये? ये धर्मो हानिर्भवति।",
    "translation": "What shall I do when performing duty causes harm?",
    "chapter": "Chapter 1, Verse 38",
    "context": "Arjuna questions the righteousness of his duty.",
    "practical_meaning": "Moral dilemmas require careful judgment.",
    "life_application": "Seek guidance and evaluate consequences before acting.",
    "keywords": ["duty", "harm", "moral dilemma", "judgment"]
  },
  {
    "shloka": "न हि प्रपश्यामि सुखं हत्वा स्वजनमाहवे।",
    "translation": "I do not see any joy in killing my own relatives.",
    "chapter": "Chapter 1, Verse 39",
    "context": "Arjuna is gripped by sorrow at the idea of killing his family.",
    "practical_meaning": "Harming loved ones brings no happiness.",
    "life_application": "Consider emotional and moral consequences in difficult decisions.",
    "keywords": ["sorrow", "family", "happiness", "consequences"]
  },
  {
    "shloka": "कुलधर्मं न हि शोभते हत्वा स्वजनमाहवे।",
    "translation": "Destroying family duty by killing relatives is inappropriate.",
    "chapter": "Chapter 1, Verse 40",
    "context": "Arjuna emphasizes dharma and the importance of family.",
    "practical_meaning": "Ethics and family duties must guide decisions.",
    "life_application": "Always prioritize ethical principles in actions affecting loved ones.",
    "keywords": ["dharma", "family", "ethics", "duty"]
  },
  {
    "shloka": "सञ्जय उवाच । अर्जुनोऽपि शोकान्वितः रथे स्थिता।",
    "translation": "Sanjaya said: Arjuna, filled with sorrow, sat down on the chariot.",
    "chapter": "Chapter 1, Verse 41",
    "context": "Overcome with grief, Arjuna becomes immobile, unable to fight.",
    "practical_meaning": "Grief and moral conflict can paralyze action.",
    "life_application": "Recognize emotional blocks and seek guidance before acting.",
    "keywords": ["grief", "paralysis", "emotion", "conflict"]
  },
  {
    "shloka": "मम आत्मा व्यथितः, न हि प्रहर्तुमिच्छामि।",
    "translation": "My soul is distressed; I do not wish to fight.",
    "chapter": "Chapter 1, Verse 42",
    "context": "Arjuna expresses his deep inner turmoil at the thought of killing his relatives.",
    "practical_meaning": "Internal conflict can overpower duty and reason.",
    "life_application": "Acknowledge inner turmoil and seek calm reflection before decisions.",
    "keywords": ["distress", "conflict", "soul", "reflection"]
  },
  {
    "shloka": "कुलनाशाय कुतः सुखं? अनर्थेषु हि सुखम्।",
    "translation": "How can there be happiness in the destruction of family? True happiness is impossible in misfortune.",
    "chapter": "Chapter 1, Verse 43",
    "context": "Arjuna laments the destruction that war brings to families.",
    "practical_meaning": "Harm to loved ones creates deep sorrow.",
    "life_application": "Avoid actions that inflict suffering on those close to you.",
    "keywords": ["happiness", "misfortune", "family", "sorrow"]
  },
  {
    "shloka": "न हि प्रपश्यामि धर्मस्य हानिमाप्नुयाम।",
    "translation": "I cannot see any righteousness in slaying my relatives.",
    "chapter": "Chapter 1, Verse 44",
    "context": "Arjuna questions the morality of his actions in battle.",
    "practical_meaning": "Actions against dharma lead to moral conflict.",
    "life_application": "Always weigh ethical implications before taking action.",
    "keywords": ["righteousness", "ethics", "dharma", "conflict"]
  },
  {
    "shloka": "अहं कृत्स्नं पापं करोमि स्वजनमाहवे।",
    "translation": "I commit complete sin by attacking my own kin.",
    "chapter": "Chapter 1, Verse 45",
    "context": "Arjuna feels that engaging in war with his family is sinful.",
    "practical_meaning": "Violating moral principles leads to inner guilt.",
    "life_application": "Act in alignment with conscience to avoid regret.",
    "keywords": ["sin", "guilt", "morality", "family"]
  },
  {
    "shloka": "सञ्जय उवाच । अर्जुनोऽपि क्लान्तः रथं प्रतिष्ठापयामास।",
    "translation": "Sanjaya said: Arjuna, exhausted and sorrowful, let his chariot remain stationary.",
    "chapter": "Chapter 1, Verse 46",
    "context": "Arjuna remains seated in the chariot, unable to act due to sorrow.",
    "practical_meaning": "Emotional overwhelm can freeze one into inaction.",
    "life_application": "Recognize when emotions hinder performance and take time to recover.",
    "keywords": ["emotion", "inaction", "sorrow", "reflection"]
  },
  {
    "shloka": "अर्जुन उवाच । गच्छामि, कृष्ण, युद्धे न हि शक्नोम्यहम्।",
    "translation": "Arjuna said: O Krishna, I shall not fight; I am unable to engage in this battle.",
    "chapter": "Chapter 1, Verse 47",
    "context": "Arjuna finally declares his inability to fight, marking the climax of his despair.",
    "practical_meaning": "Acknowledging one’s limits is crucial in times of moral crisis.",
    "life_application": "It is okay to pause and seek counsel when overwhelmed by difficult choices.",
    "keywords": ["limits", "pause", "moral crisis", "reflection"]
  },
  {
    "shloka": "सञ्जय उवाच । तं तथा कृपयाश्रुतं स्वभावोपस्थितं हृषीकेशम्।",
    "translation": "Sanjaya said: Seeing Arjuna overwhelmed with compassion and sorrow, Krishna, the master of the senses, spoke.",
    "chapter": "Chapter 2, Verse 1",
    "context": "Krishna notices Arjuna’s grief and prepares to counsel him.",
    "practical_meaning": "Guidance comes at moments of despair.",
    "life_application": "Seek wisdom and support during emotional crises.",
    "keywords": ["guidance", "compassion", "sorrow", "wisdom"]
  },
  {
    "shloka": "कुतस्त्वा कश्मलमिदं विषमे समुपस्थितम्।",
    "translation": "Arjuna said: My mind is confused; how has this weakness come upon me in this critical moment?",
    "chapter": "Chapter 2, Verse 2",
    "context": "Arjuna expresses confusion and moral dilemma.",
    "practical_meaning": "Even great individuals face uncertainty under pressure.",
    "life_application": "Acknowledge mental blocks and seek clarity before acting.",
    "keywords": ["confusion", "pressure", "dilemma", "reflection"]
  },
  {
    "shloka": "न हि प्रपश्यामि मम जन्मभूमौ परिवार्यं।",
    "translation": "I cannot see any benefit in killing my own relatives on this battlefield.",
    "chapter": "Chapter 2, Verse 3",
    "context": "Arjuna laments the potential destruction of his family.",
    "practical_meaning": "Harming loved ones brings moral conflict.",
    "life_application": "Consider the consequences of actions on loved ones.",
    "keywords": ["family", "harm", "consequences", "reflection"]
  },
  {
    "shloka": "कुलनाशाय कुतः सुखं? अनर्थेषु हि सुखम्।",
    "translation": "How can there be happiness in the destruction of family? True happiness cannot come from misfortune.",
    "chapter": "Chapter 2, Verse 4",
    "context": "Arjuna reflects on the sorrow caused by family destruction.",
    "practical_meaning": "Harming loved ones creates deep suffering.",
    "life_application": "Avoid actions that inflict harm on others.",
    "keywords": ["happiness", "misfortune", "family", "sorrow"]
  },
  {
    "shloka": "धर्मं हि मम प्रियं न हि प्रपश्यामि सुखम्।",
    "translation": "I cannot see happiness in performing a duty that causes harm.",
    "chapter": "Chapter 2, Verse 5",
    "context": "Arjuna highlights the conflict between duty and moral ethics.",
    "practical_meaning": "Ethical dilemmas can create inner conflict.",
    "life_application": "Always align actions with ethical principles.",
    "keywords": ["duty", "ethics", "conflict", "happiness"]
  },
  {
    "shloka": "मम पाण्डवाः संगीता युद्धे प्रियजनम्।",
    "translation": "My relatives, friends, and teachers stand ready for battle.",
    "chapter": "Chapter 2, Verse 6",
    "context": "Arjuna notices the presence of loved ones on the battlefield.",
    "practical_meaning": "Facing conflict with loved ones present increases emotional burden.",
    "life_application": "Recognize emotional stakes before making difficult decisions.",
    "keywords": ["loved ones", "conflict", "emotional burden", "reflection"]
  },
  {
    "shloka": "सञ्जय उवाच । अर्जुनोऽपि शोकान्वितः रथे स्थिता।",
    "translation": "Sanjaya said: Arjuna, overwhelmed with grief, sat down on the chariot.",
    "chapter": "Chapter 2, Verse 7",
    "context": "Arjuna reaches the peak of despair and inaction.",
    "practical_meaning": "Emotional overwhelm can freeze decision-making.",
    "life_application": "Pause and seek guidance when paralyzed by emotion.",
    "keywords": ["grief", "inaction", "decision-making", "emotion"]
  },
  {
    "shloka": "कृष्ण उवाच । कायं कर्मणि व्यथितं मा कुरु।",
    "translation": "Krishna said: Do not grieve for the body; it is merely the instrument for action.",
    "chapter": "Chapter 2, Verse 8",
    "context": "Krishna begins teaching Arjuna about the immortality of the soul.",
    "practical_meaning": "Focus on actions, not attachment to outcomes or the temporary body.",
    "life_application": "Detach from fear and grief regarding temporary losses.",
    "keywords": ["soul", "detachment", "action", "grief"]
  },
  {
    "shloka": "नैव तस्य हि जीवितं क्षीयते, न हि पश्यसि।",
    "translation": "The soul neither kills nor can be killed; it is eternal.",
    "chapter": "Chapter 2, Verse 9",
    "context": "Krishna explains the eternal nature of the soul.",
    "practical_meaning": "Understanding the eternal perspective reduces fear and sorrow.",
    "life_application": "Focus on enduring values rather than temporary setbacks.",
    "keywords": ["soul", "eternal", "fear", "perspective"]
  },
  {
    "shloka": "अशोकं हि न हि कर्मणि व्यथितं कुरु।",
    "translation": "Do your duty without attachment or sorrow.",
    "chapter": "Chapter 2, Verse 10",
    "context": "Krishna advises performing action with equanimity.",
    "practical_meaning": "Work diligently but without attachment to results.",
    "life_application": "Focus on effort and skill rather than outcomes.",
    "keywords": ["duty", "equanimity", "detachment", "action"]
  },
  {
    "shloka": "श्रीभगवानुवाच । अजेयं शाश्वतं नित्यं, न हि जीवितं क्षीयते।",
    "translation": "The Blessed Lord said: The soul is imperishable, eternal, and never dies.",
    "chapter": "Chapter 2, Verse 11",
    "context": "Krishna begins teaching Arjuna about the immortality of the soul.",
    "practical_meaning": "Understanding the eternal nature of the self removes fear of loss.",
    "life_application": "Focus on spiritual growth and values rather than temporary concerns.",
    "keywords": ["soul", "eternal", "immortality", "fear"]
  },
  {
    "shloka": "कायं न हि तुहिनं क्षीयते, न हि पश्यसि।",
    "translation": "The body may perish, but the soul never dies.",
    "chapter": "Chapter 2, Verse 12",
    "context": "Krishna clarifies the distinction between the temporary body and eternal soul.",
    "practical_meaning": "Detach from fear of death; focus on the eternal essence.",
    "life_application": "Live mindfully, realizing that challenges are temporary.",
    "keywords": ["body", "soul", "detachment", "impermanence"]
  },
  {
    "shloka": "न जायते म्रियते वा कदाचि।",
    "translation": "The soul is never born and never dies.",
    "chapter": "Chapter 2, Verse 13",
    "context": "Krishna explains the eternal continuity of the soul through cycles of life.",
    "practical_meaning": "Life and death are only transitions of the body, not the soul.",
    "life_application": "Do not fear change; see it as part of the natural cycle.",
    "keywords": ["soul", "birth", "death", "continuity"]
  },
  {
    "shloka": "यदाहं पाण्डवाः प्रपद्ये।",
    "translation": "Just as the soul passes from one body to another, so does consciousness continue.",
    "chapter": "Chapter 2, Verse 14",
    "context": "Krishna uses the analogy of changing clothes to explain reincarnation.",
    "practical_meaning": "Change is natural and the soul remains untouched.",
    "life_application": "Accept life’s transitions without attachment or fear.",
    "keywords": ["reincarnation", "change", "consciousness", "acceptance"]
  },
  {
    "shloka": "कर्मण्येवाधिकारस्ते मा फलेषु कदाचन।",
    "translation": "You have a right to perform your prescribed duty, but not to the fruits of action.",
    "chapter": "Chapter 2, Verse 15",
    "context": "Krishna introduces the principle of Karma Yoga.",
    "practical_meaning": "Focus on effort, not outcomes.",
    "life_application": "Do your best in studies, work, or projects without worrying about results.",
    "keywords": ["karma", "duty", "detachment", "effort"]
  },
  {
    "shloka": "मा कर्मफलहेतुर्भूर्मा ते सङ्गोऽस्त्वकर्मणि।",
    "translation": "Do not act for the sake of results, and do not be attached to inaction.",
    "chapter": "Chapter 2, Verse 16",
    "context": "Krishna emphasizes detachment from results while remaining active.",
    "practical_meaning": "Avoid obsession with outcomes but continue performing your duties.",
    "life_application": "Stay diligent without anxiety about success or failure.",
    "keywords": ["detachment", "karma", "action", "results"]
  },
  {
    "shloka": "योगस्थः कुरु कर्माणि सङ्गं त्यक्त्वा धनञ्जय।",
    "translation": "Perform your duty while remaining steadfast in yoga, abandoning attachment.",
    "chapter": "Chapter 2, Verse 17",
    "context": "Krishna teaches Arjuna the essence of yoga – equanimity in action.",
    "practical_meaning": "Balance work with mental calm and detachment.",
    "life_application": "Approach challenges with composure, regardless of outcomes.",
    "keywords": ["yoga", "equanimity", "duty", "detachment"]
  },
  {
    "shloka": "सिद्ध्यसिद्ध्योः समो भूत्वा समत्वं योग उच्यते।",
    "translation": "Equanimity in success and failure is called yoga.",
    "chapter": "Chapter 2, Verse 18",
    "context": "Krishna explains that yoga is mental balance amidst dualities.",
    "practical_meaning": "Stay calm whether you win or lose.",
    "life_application": "Maintain stability in emotions when facing ups and downs.",
    "keywords": ["equanimity", "yoga", "balance", "success", "failure"]
  },
  {
    "shloka": "यदा तु न मंशा व्यथते हि मनः।",
    "translation": "When the mind is not disturbed by adversity, it attains yoga.",
    "chapter": "Chapter 2, Verse 19",
    "context": "Mental stability is key to spiritual and practical success.",
    "practical_meaning": "A calm mind makes better decisions.",
    "life_application": "Practice mindfulness and emotional regulation.",
    "keywords": ["mind", "stability", "yoga", "adversity"]
  },
  {
    "shloka": "अज्ञानेन तमसि जातस्य।",
    "translation": "The person who acts in ignorance is entangled in darkness.",
    "chapter": "Chapter 2, Verse 20",
    "context": "Krishna warns against action without knowledge.",
    "practical_meaning": "Acting without understanding leads to mistakes.",
    "life_application": "Seek knowledge and awareness before taking action.",
    "keywords": ["ignorance", "knowledge", "action", "awareness"]
  },
  {
    "shloka": "वासांसि जीर्णानि यथा विहाय।",
    "translation": "Just as a person casts off worn-out clothes and puts on new ones, so does the soul discard worn-out bodies and take on new ones.",
    "chapter": "Chapter 2, Verse 21",
    "context": "Krishna explains the eternal nature of the soul through the analogy of clothing.",
    "practical_meaning": "Life is a continuous process of change; the soul remains untouched.",
    "life_application": "Do not fear change or death; focus on the eternal self.",
    "keywords": ["soul", "change", "rebirth", "impermanence"]
  },
  {
    "shloka": "न त्वहं कामये राज्यं न स्वर्गं नापुनर्भवम्।",
    "translation": "I do not desire kingdom, heaven, or liberation, O Arjuna.",
    "chapter": "Chapter 2, Verse 22",
    "context": "Krishna emphasizes performing duty for duty’s sake, not for reward.",
    "practical_meaning": "Detachment from results is key to spiritual and practical success.",
    "life_application": "Work sincerely without expecting rewards.",
    "keywords": ["detachment", "duty", "reward", "spirituality"]
  },
  {
    "shloka": "न जायते म्रियते वा कदाचि।",
    "translation": "The soul is neither born nor does it ever die.",
    "chapter": "Chapter 2, Verse 23",
    "context": "Krishna clarifies the eternal, indestructible nature of the soul.",
    "practical_meaning": "Understanding the permanence of the soul alleviates fear.",
    "life_application": "Focus on eternal values rather than temporary losses.",
    "keywords": ["soul", "eternal", "immortality", "fear"]
  },
  {
    "shloka": "न हन्यते हन्यमाने शरीरे।",
    "translation": "The soul is not harmed when the body is killed.",
    "chapter": "Chapter 2, Verse 24",
    "context": "Krishna explains that the body is temporary but the soul is eternal.",
    "practical_meaning": "Detach from fear of bodily harm; the essence remains intact.",
    "life_application": "Prioritize long-term values over temporary fears.",
    "keywords": ["soul", "body", "detachment", "fear"]
  },
  {
    "shloka": "अविनाशी तु तद्विद्धि यत्त्वं सर्वमितीश्वरम्।",
    "translation": "Know the soul to be imperishable and eternal, beyond birth and death.",
    "chapter": "Chapter 2, Verse 25",
    "context": "Krishna stresses knowledge of the eternal self as crucial for peace.",
    "practical_meaning": "Recognizing permanence reduces anxiety and grief.",
    "life_application": "Focus on spiritual understanding to face life’s challenges calmly.",
    "keywords": ["soul", "eternal", "knowledge", "peace"]
  },
  {
    "shloka": "अन्तवः कर्माणि न तस्य।",
    "translation": "The soul is not affected by actions or their results.",
    "chapter": "Chapter 2, Verse 26",
    "context": "Krishna teaches that the true self remains untouched by worldly activities.",
    "practical_meaning": "Detachment from outcomes provides stability and clarity.",
    "life_application": "Perform duties but do not be emotionally bound to results.",
    "keywords": ["detachment", "actions", "results", "soul"]
  },
  {
    "shloka": "नैव हि ज्ञानेन सदृशं पवित्रमिह विद्यते।",
    "translation": "There is nothing as purifying as knowledge in this world.",
    "chapter": "Chapter 2, Verse 27",
    "context": "Krishna emphasizes that knowledge leads to liberation and peace.",
    "practical_meaning": "Knowledge dispels fear, confusion, and sorrow.",
    "life_application": "Seek wisdom to navigate life effectively.",
    "keywords": ["knowledge", "wisdom", "purity", "liberation"]
  },
  {
    "shloka": "योगिनः कर्मकौशलमुपयान्ति।",
    "translation": "Yogis attain skill in action by acting with equanimity.",
    "chapter": "Chapter 2, Verse 28",
    "context": "Krishna introduces Karma Yoga – acting without attachment to results.",
    "practical_meaning": "Equanimity in action leads to mastery and peace.",
    "life_application": "Do your duties calmly, without emotional disturbance.",
    "keywords": ["karma", "yoga", "equanimity", "action"]
  },
  {
    "shloka": "सर्वकर्माणि संन्यस्य।",
    "translation": "Renouncing the attachment to all actions, one attains liberation.",
    "chapter": "Chapter 2, Verse 29",
    "context": "Krishna explains that detachment from results leads to freedom.",
    "practical_meaning": "Detach from the fruits of work, not from work itself.",
    "life_application": "Focus on effort, not on outcomes.",
    "keywords": ["detachment", "liberation", "karma", "action"]
  },
  {
    "shloka": "योगः कर्मसु कौशलम्।",
    "translation": "Yoga is skill in action, achieved through mindfulness and detachment.",
    "chapter": "Chapter 2, Verse 30",
    "context": "Krishna defines yoga as excellence in action without attachment.",
    "practical_meaning": "Performing duties with focus and detachment is true yoga.",
    "life_application": "Excel in your responsibilities while remaining emotionally balanced.",
    "keywords": ["yoga", "skill", "action", "detachment"]
  },
    {
    "shloka": "श्रीभगवानुवाच । शस्त्रयोः कर्तव्यं धर्मम् अर्जुन।",
    "translation": "The Blessed Lord said: O Arjuna, it is your duty as a warrior to fight righteous war.",
    "chapter": "Chapter 2, Verse 31",
    "context": "Krishna reminds Arjuna of his Kshatriya duty to fight for justice.",
    "practical_meaning": "Perform your responsibilities according to your role and dharma.",
    "life_application": "Understand and fulfill your duties without attachment to results.",
    "keywords": ["duty", "warrior", "karma", "righteousness"]
  },
  {
    "shloka": "यदा धर्मो हानिः स्यात्, ते कर्मणि न विलम्ब।",
    "translation": "When righteousness is at stake, do not hesitate in action.",
    "chapter": "Chapter 2, Verse 32",
    "context": "Krishna emphasizes acting decisively when dharma is threatened.",
    "practical_meaning": "Ethical duties demand prompt action.",
    "life_application": "Act without delay when justice or morality is involved.",
    "keywords": ["righteousness", "action", "ethics", "duty"]
  },
  {
    "shloka": "कुलधर्मे निधनं श्रेयः परधर्मो भयावहः।",
    "translation": "It is better to die performing one’s own duty than to perform another’s duty.",
    "chapter": "Chapter 2, Verse 33",
    "context": "Krishna advises following one’s own dharma even at risk.",
    "practical_meaning": "Authenticity and duty to oneself are paramount.",
    "life_application": "Focus on your responsibilities rather than comparing to others.",
    "keywords": ["dharma", "authenticity", "duty", "courage"]
  },
  {
    "shloka": "सत्त्वं ज्ञानयोगे स्थितो यः स इत्यभिधीयते।",
    "translation": "One established in the yoga of knowledge is said to be in sattva.",
    "chapter": "Chapter 2, Verse 34",
    "context": "Krishna introduces the qualities of a wise person focused on knowledge and action.",
    "practical_meaning": "Knowledge brings clarity and steadiness of mind.",
    "life_application": "Cultivate wisdom and balance in all actions.",
    "keywords": ["knowledge", "yoga", "wisdom", "balance"]
  },
  {
    "shloka": "कर्मण्येवाधिकारस्ते मा फलेषु कदाचन।",
    "translation": "You have the right to work only, never to its fruits.",
    "chapter": "Chapter 2, Verse 35",
    "context": "Krishna repeats the principle of Karma Yoga.",
    "practical_meaning": "Focus on effort rather than outcome.",
    "life_application": "Work diligently and accept results without attachment.",
    "keywords": ["karma", "effort", "detachment", "action"]
  },
  {
    "shloka": "मा ते सङ्गोऽस्त्वकर्मणि।",
    "translation": "Do not be attached to inaction.",
    "chapter": "Chapter 2, Verse 36",
    "context": "Krishna advises against shirking responsibilities.",
    "practical_meaning": "Detachment does not mean avoiding action.",
    "life_application": "Engage fully in duties without obsessing over outcomes.",
    "keywords": ["detachment", "action", "responsibility", "karma"]
  },
  {
    "shloka": "योगस्थः कुरु कर्माणि सङ्गं त्यक्त्वा धनञ्जय।",
    "translation": "Perform duties while remaining steadfast in yoga, abandoning attachment.",
    "chapter": "Chapter 2, Verse 37",
    "context": "Krishna teaches Arjuna to act with mental balance and focus.",
    "practical_meaning": "Balance action with detachment for mental stability.",
    "life_application": "Handle work with composure and focus.",
    "keywords": ["yoga", "equanimity", "action", "detachment"]
  },
  {
    "shloka": "सिद्ध्यसिद्ध्योः समो भूत्वा समत्वं योग उच्यते।",
    "translation": "Evenness of mind in success and failure is called yoga.",
    "chapter": "Chapter 2, Verse 38",
    "context": "Krishna defines yoga as maintaining balance amid dualities.",
    "practical_meaning": "Stay calm whether you win or lose.",
    "life_application": "Maintain emotional stability in all circumstances.",
    "keywords": ["equanimity", "yoga", "balance", "success", "failure"]
  },
  {
    "shloka": "ज्ञानी च युक्तः कर्त्तव्यं कर्म यथोक्तम्।",
    "translation": "A person of knowledge performs prescribed duties properly.",
    "chapter": "Chapter 2, Verse 39",
    "context": "Krishna emphasizes acting according to dharma with wisdom.",
    "practical_meaning": "Knowledge guides right action.",
    "life_application": "Act with understanding and mindfulness in responsibilities.",
    "keywords": ["knowledge", "duty", "wisdom", "karma"]
  },
  {
    "shloka": "नियतं कर्म कुर्वन्तः सङ्गं त्यक्त्वा फलानुमानम्।",
    "translation": "Performing fixed duties while abandoning attachment to outcomes brings peace.",
    "chapter": "Chapter 2, Verse 40",
    "context": "Krishna explains the path of Karma Yoga for stability and liberation.",
    "practical_meaning": "Detachment from results while performing duties leads to contentment.",
    "life_application": "Focus on consistent effort rather than rewards.",
    "keywords": ["karma", "detachment", "peace", "duty"]
  },
  {
    "shloka": "युक्त: कर्मफलत्यागी सन्तुष्ट: सततं योगी।",
    "translation": "One who is devoted, abandons the fruits of action, and is ever content is called a yogi.",
    "chapter": "Chapter 2, Verse 41",
    "context": "Krishna explains the qualities of a yogi focused on contentment and detachment.",
    "practical_meaning": "Detachment and satisfaction in effort define a disciplined mind.",
    "life_application": "Practice contentment and avoid obsession with outcomes.",
    "keywords": ["yogi", "detachment", "contentment", "discipline"]
  },
  {
    "shloka": "सुखं वा दुःखं वा समं कर्म करोति य:।",
    "translation": "One who performs duty with equanimity in pleasure and pain is a true yogi.",
    "chapter": "Chapter 2, Verse 42",
    "context": "Maintaining balance in all experiences is essential for spiritual growth.",
    "practical_meaning": "Equanimity in success or failure promotes mental stability.",
    "life_application": "Stay steady-minded regardless of external circumstances.",
    "keywords": ["equanimity", "yogi", "balance", "stability"]
  },
  {
    "shloka": "सर्वकर्माणि संयमी यः स योगी सदा स्थितः।",
    "translation": "He who controls all actions and remains steady is always called a yogi.",
    "chapter": "Chapter 2, Verse 43",
    "context": "Krishna emphasizes self-control as the mark of a yogi.",
    "practical_meaning": "Discipline in actions fosters inner peace and mastery.",
    "life_application": "Practice self-control in all aspects of life.",
    "keywords": ["self-control", "yogi", "discipline", "actions"]
  },
  {
    "shloka": "ज्ञानी च युक्तः सर्वकर्मसु।",
    "translation": "A wise person performs all duties skillfully and without attachment.",
    "chapter": "Chapter 2, Verse 44",
    "context": "Knowledge combined with detachment ensures proper execution of duties.",
    "practical_meaning": "Wisdom enables focused and effective action.",
    "life_application": "Use knowledge to perform tasks efficiently without obsession over results.",
    "keywords": ["wisdom", "detachment", "skill", "duty"]
  },
  {
    "shloka": "यः सर्वत्र समः सुखं दुःखं च।",
    "translation": "He who remains the same in pleasure and pain is truly a yogi.",
    "chapter": "Chapter 2, Verse 45",
    "context": "Equanimity in all situations is central to spiritual discipline.",
    "practical_meaning": "Stability of mind is more valuable than external success.",
    "life_application": "Practice emotional balance in every circumstance.",
    "keywords": ["equanimity", "yogi", "pleasure", "pain"]
  },
  {
    "shloka": "विवेकं च योगिनः सदा सुखम्।",
    "translation": "Discerning yoga leads to enduring happiness.",
    "chapter": "Chapter 2, Verse 46",
    "context": "Krishna teaches that wisdom and discernment bring lasting peace.",
    "practical_meaning": "Understanding the true nature of reality reduces suffering.",
    "life_application": "Cultivate discernment and awareness to maintain inner peace.",
    "keywords": ["wisdom", "discernment", "yoga", "happiness"]
  },
  {
    "shloka": "सर्वकर्माणि मं योगिनः सदा समः।",
    "translation": "A yogi remains balanced in performing all actions.",
    "chapter": "Chapter 2, Verse 47",
    "context": "Balance in action defines spiritual maturity.",
    "practical_meaning": "Stay balanced and unattached in work.",
    "life_application": "Focus on doing your duties without being emotionally swayed.",
    "keywords": ["balance", "yogi", "action", "detachment"]
  },
  {
    "shloka": "योगिनः कर्मसु कौशलमुपयान्ति।",
    "translation": "Yogis attain skill in action by practicing detachment.",
    "chapter": "Chapter 2, Verse 48",
    "context": "Krishna reinforces Karma Yoga principles.",
    "practical_meaning": "Detachment enhances efficiency and mastery.",
    "life_application": "Practice work with focus and detachment for better outcomes.",
    "keywords": ["karma", "skill", "yogi", "detachment"]
  },
  {
    "shloka": "विवेकं च योगिनः सदा सुखम्।",
    "translation": "Discernment leads the yogi to happiness.",
    "chapter": "Chapter 2, Verse 49",
    "context": "Krishna emphasizes mindfulness and insight.",
    "practical_meaning": "Knowledge and awareness guide proper action.",
    "life_application": "Develop mindfulness to act wisely in all circumstances.",
    "keywords": ["discernment", "yogi", "happiness", "awareness"]
  },
  {
    "shloka": "सर्वत्र समत्वं योगिनः स्थिरम्।",
    "translation": "A yogi remains steady and balanced in all situations.",
    "chapter": "Chapter 2, Verse 50",
    "context": "Krishna concludes this segment emphasizing mental stability and detachment.",
    "practical_meaning": "Balance and steadiness are the hallmarks of wisdom.",
    "life_application": "Aim for calmness and balance, regardless of external circumstances.",
    "keywords": ["balance", "steadiness", "yogi", "wisdom"]
  },
  {
    "shloka": "यदा संन्यस्त: सर्गे कर्म च।",
    "translation": "When one renounces attachment to action and performs duty with equanimity, they attain yoga.",
    "chapter": "Chapter 2, Verse 51",
    "context": "Krishna teaches that detachment in action leads to mastery and peace.",
    "practical_meaning": "Detach from outcomes to perform duties skillfully.",
    "life_application": "Work sincerely without craving results.",
    "keywords": ["detachment", "yoga", "action", "skill"]
  },
  {
    "shloka": "सर्वकर्माणि संन्यस्य।",
    "translation": "By abandoning attachment to all actions, one becomes free from bondage.",
    "chapter": "Chapter 2, Verse 52",
    "context": "Renunciation of attachment purifies the mind.",
    "practical_meaning": "Freedom comes from letting go of personal desires in action.",
    "life_application": "Focus on duty, not on personal gain.",
    "keywords": ["renunciation", "freedom", "attachment", "duty"]
  },
  {
    "shloka": "सुखदुःखे समं कृत्वा।",
    "translation": "Treat pleasure and pain equally, remaining balanced in all situations.",
    "chapter": "Chapter 2, Verse 53",
    "context": "Equanimity is central to the yogi’s practice.",
    "practical_meaning": "Maintain calm and composure in any circumstance.",
    "life_application": "Do not let emotions control your actions.",
    "keywords": ["equanimity", "balance", "pleasure", "pain"]
  },
  {
    "shloka": "असंन्यस्त: संन्यासी य:।",
    "translation": "Even if performing actions, one who is unattached is considered a true renunciate.",
    "chapter": "Chapter 2, Verse 54",
    "context": "Krishna explains that renunciation is mental, not physical.",
    "practical_meaning": "Detachment defines spiritual progress.",
    "life_application": "Act without attachment while remaining engaged in life.",
    "keywords": ["renunciation", "detachment", "karma", "spirituality"]
  },
  {
    "shloka": "योगिन: संन्यस्तकर्मण:।",
    "translation": "Yogis who perform duties without attachment reach higher understanding.",
    "chapter": "Chapter 2, Verse 55",
    "context": "Yogis act while maintaining inner peace and focus.",
    "practical_meaning": "Balanced action leads to clarity and liberation.",
    "life_application": "Practice mindfulness and detachment in daily tasks.",
    "keywords": ["yogi", "detachment", "clarity", "karma"]
  },
  {
    "shloka": "व्यासवद्विद्या हि योगिनाम्।",
    "translation": "Knowledge is the path for yogis to transcend worldly bondage.",
    "chapter": "Chapter 2, Verse 56",
    "context": "Krishna emphasizes learning and wisdom as the foundation of yoga.",
    "practical_meaning": "Knowledge guides action and frees from confusion.",
    "life_application": "Prioritize learning and insight in all endeavors.",
    "keywords": ["knowledge", "yoga", "freedom", "wisdom"]
  },
  {
    "shloka": "न हि देहेनैव जीवितं।",
    "translation": "Life is not defined by the body; the soul transcends the physical form.",
    "chapter": "Chapter 2, Verse 57",
    "context": "Krishna reminds Arjuna that the soul is eternal.",
    "practical_meaning": "Detach from the body and material concerns.",
    "life_application": "Focus on spiritual and inner development.",
    "keywords": ["soul", "body", "eternal", "detachment"]
  },
  {
    "shloka": "संन्यास: कर्मयोगे च।",
    "translation": "Renunciation and Karma Yoga are not opposed; both lead to liberation.",
    "chapter": "Chapter 2, Verse 58",
    "context": "Krishna explains that performing duties with detachment is true renunciation.",
    "practical_meaning": "Action with detachment is equivalent to spiritual renunciation.",
    "life_application": "Do your work without selfish motives to achieve inner peace.",
    "keywords": ["karma", "renunciation", "detachment", "liberation"]
  },
  {
    "shloka": "संतुष्ट: य: सदा।",
    "translation": "One who is always content is a yogi.",
    "chapter": "Chapter 2, Verse 59",
    "context": "Contentment is a key quality of a balanced mind.",
    "practical_meaning": "Happiness comes from inner contentment, not external gains.",
    "life_application": "Practice gratitude and satisfaction in daily life.",
    "keywords": ["contentment", "yogi", "happiness", "balance"]
  },
  {
    "shloka": "श्रीभगवानुवाच।",
    "translation": "The Blessed Lord said: Those who act without attachment transcend sorrow.",
    "chapter": "Chapter 2, Verse 60",
    "context": "Krishna concludes this segment emphasizing detachment in action.",
    "practical_meaning": "Freedom from attachment reduces suffering.",
    "life_application": "Act diligently while letting go of personal desires.",
    "keywords": ["detachment", "action", "freedom", "sorrow"]
  },
  {
    "shloka": "ध्यायतो विषयान्पुंसः।",
    "translation": "A person who meditates on sense objects develops attachment and suffering.",
    "chapter": "Chapter 2, Verse 61",
    "context": "Krishna warns about the mind’s tendency to get entangled with sensory pleasures.",
    "practical_meaning": "Attachment to fleeting pleasures causes pain.",
    "life_application": "Practice mindfulness and control over desires.",
    "keywords": ["mind", "attachment", "senses", "desires"]
  },
  {
    "shloka": "संस्पृष्टविषयं ध्यानात्स्वल्पम्।",
    "translation": "Through meditation on objects of the senses, desire grows stronger.",
    "chapter": "Chapter 2, Verse 62",
    "context": "Krishna explains how unchecked focus on sensory objects leads to craving.",
    "practical_meaning": "Uncontrolled desire leads to frustration.",
    "life_application": "Train the mind to focus on higher goals rather than temporary pleasures.",
    "keywords": ["desire", "craving", "focus", "mind"]
  },
  {
    "shloka": "कामसंयोगात्सङ्गोऽनुभवतः।",
    "translation": "Attachment from desire leads to anger when expectations are unmet.",
    "chapter": "Chapter 2, Verse 63",
    "context": "Desire, when frustrated, turns into anger and suffering.",
    "practical_meaning": "Unchecked desire leads to negative emotions.",
    "life_application": "Practice detachment and manage emotional reactions.",
    "keywords": ["anger", "desire", "attachment", "emotions"]
  },
  {
    "shloka": "क्रोधाद्भवति सम्मोहः।",
    "translation": "From anger comes delusion, and from delusion, loss of memory and reasoning.",
    "chapter": "Chapter 2, Verse 64",
    "context": "Krishna explains the chain reaction from desire to confusion and error.",
    "practical_meaning": "Negative emotions cloud judgment.",
    "life_application": "Stay calm to maintain clarity and make wise decisions.",
    "keywords": ["anger", "delusion", "confusion", "judgment"]
  },
  {
    "shloka": "सङ्क्षेपेण हि ज्ञानेन।",
    "translation": "Knowledge and self-control free one from this chain of suffering.",
    "chapter": "Chapter 2, Verse 65",
    "context": "Krishna teaches that wisdom and detachment prevent negative cycles.",
    "practical_meaning": "Understanding and mindfulness break destructive patterns.",
    "life_application": "Cultivate awareness and detachment to avoid emotional pitfalls.",
    "keywords": ["knowledge", "self-control", "detachment", "freedom"]
  },
  {
    "shloka": "योगिनो हि सदा।",
    "translation": "A yogi remains balanced, whether in pleasure or pain.",
    "chapter": "Chapter 2, Verse 66",
    "context": "Equanimity is essential for spiritual progress.",
    "practical_meaning": "Balance in emotions leads to stability.",
    "life_application": "Practice calmness in all situations.",
    "keywords": ["yogi", "equanimity", "balance", "stability"]
  },
  {
    "shloka": "दुःखेष्वनुद्विग्नमनाः।",
    "translation": "One who is not disturbed in sorrow and remains steady in happiness is a wise person.",
    "chapter": "Chapter 2, Verse 67",
    "context": "Krishna emphasizes the steadiness of mind in all experiences.",
    "practical_meaning": "Emotional resilience is a mark of wisdom.",
    "life_application": "Practice emotional regulation and mental stability.",
    "keywords": ["wisdom", "resilience", "happiness", "sorrow"]
  },
  {
    "shloka": "सुखेषु विगतस्पृहः।",
    "translation": "Free from desire for pleasure, fear, and anger, the sage attains peace.",
    "chapter": "Chapter 2, Verse 68",
    "context": "Krishna describes the qualities of a person with steady wisdom.",
    "practical_meaning": "Detachment from extreme emotions brings calmness.",
    "life_application": "Avoid attachment to outcomes to remain peaceful.",
    "keywords": ["detachment", "peace", "anger", "fear"]
  },
  {
    "shloka": "स्थितधीर्मुनिरुच्यते।",
    "translation": "A person with steady wisdom is called a sage.",
    "chapter": "Chapter 2, Verse 69",
    "context": "Krishna defines the ideal of a steady-minded individual.",
    "practical_meaning": "Inner stability and wisdom define a true sage.",
    "life_application": "Cultivate steadiness in thought and action.",
    "keywords": ["sage", "wisdom", "stability", "mind"]
  },
  {
    "shloka": "यः सर्वत्र समः।",
    "translation": "One who remains balanced in all situations achieves true yoga.",
    "chapter": "Chapter 2, Verse 70",
    "context": "Krishna concludes the teachings on steadiness and detachment.",
    "practical_meaning": "Equanimity is essential for spiritual growth.",
    "life_application": "Practice mental balance in daily life.",
    "keywords": ["yoga", "equanimity", "balance", "spiritual growth"]
  },
  {
    "shloka": "सुखदुःखे समं कृत्वा।",
    "translation": "By treating pleasure and pain equally, one transcends worldly bondage.",
    "chapter": "Chapter 2, Verse 71",
    "context": "Krishna reinforces the importance of equanimity.",
    "practical_meaning": "Balance in emotions frees the mind from attachment.",
    "life_application": "Stay calm and undisturbed in all situations.",
    "keywords": ["pleasure", "pain", "equanimity", "freedom"]
  },
  {
    "shloka": "बुद्धियोगं त्यक्त्वा।",
    "translation": "By abandoning attachment and practicing the yoga of knowledge, one attains peace.",
    "chapter": "Chapter 2, Verse 72",
    "context": "Krishna concludes the Sankhya Yoga teaching.",
    "practical_meaning": "Detachment and wisdom lead to liberation.",
    "life_application": "Focus on understanding, detachment, and mindful action.",
    "keywords": ["detachment", "knowledge", "yoga", "peace"]
  }
]

        
        # Leadership wisdom from Indian personalities
        self.inspire_quotes = [
            {
                "person": "Dr. APJ Abdul Kalam",
                "quote": "Dream is not that which you see while sleeping, it is something that does not let you sleep.",
                "context": "The importance of having passionate dreams and working towards them",
                "lesson": "Find your passion and let it drive you towards excellence"
            },
            {
                "person": "Swami Vivekananda",
                "quote": "Arise, awake, and stop not till the goal is reached.",
                "context": "From the Katha Upanishad, popularized by Vivekananda",
                "lesson": "Persistence and determination are key to overcoming any challenge"
            },
            {
                "person": "Mahatma Gandhi",
                "quote": "Be the change you wish to see in the world.",
                "context": "Personal transformation as the foundation for social change",
                "lesson": "Start with yourself before trying to change others or circumstances"
            },
            {
                "person": "Chandragupta Maurya (via Chanakya)",
                "quote": "A person should not be too honest. Straight trees are cut first.",
                "context": "Strategic wisdom from Arthashastra",
                "lesson": "Sometimes tactical wisdom is needed while maintaining ethical principles"
            }
        ]
        
        # Epic stories and lessons
        self.epic_stories = [
            {
                "epic": "Mahabharata",
                "story": "The Story of Dronacharya's Test",
                "lesson": "When Dronacharya asked his students to aim at a bird's eye, only Arjuna could see just the eye while others saw the whole bird. This teaches us about focus and concentration.",
                "application": "In life, when you're overwhelmed, focus on one thing at a time. Complete concentration leads to mastery.",
                "psychological_insight": "This relates to the concept of 'flow state' in psychology - complete immersion in an activity."
            },
            {
                "epic": "Ramayana",
                "story": "Hanuman's Leap to Lanka",
                "lesson": "When reminded of his powers, Hanuman leaped across the ocean. We often forget our own capabilities during tough times.",
                "application": "Sometimes we need others to remind us of our strengths. Don't underestimate yourself.",
                "psychological_insight": "This connects to self-efficacy theory - belief in one's ability to succeed in specific situations."
            },
            {
                "epic": "Upanishads",
                "story": "The Story of Salt in Water",
                "lesson": "A father asked his son to dissolve salt in water, then taste it. Though invisible, the salt was everywhere. Similarly, the divine is present in everything.",
                "application": "Even when you can't see solutions, they exist around you. Look deeper.",
                "psychological_insight": "This relates to mindfulness and finding meaning in difficult circumstances."
            }
        ]
        
        # Additional wisdom datasets for smart selection
        self.vedic_wisdom = [
            {
                "source": "Rig Veda",
                "quote": "Let noble thoughts come to us from every side",
                "context": "Ancient Vedic wisdom about openness to learning",
                "lesson": "Stay open to wisdom from all sources and perspectives",
                "keywords": ["learning", "wisdom", "openness", "knowledge", "growth"]
            },
            {
                "source": "Atharva Veda",
                "quote": "May all beings be happy and free from suffering",
                "context": "Universal compassion and well-being",
                "lesson": "Wish well for all beings, including yourself",
                "keywords": ["compassion", "happiness", "suffering", "well-being", "universal"]
            }
        ]
        
        self.yoga_philosophy = [
            {
                "concept": "Yamas (Ethical Guidelines)",
                "principle": "Ahimsa (Non-violence)",
                "explanation": "Non-violence in thought, word, and deed",
                "application": "Practice kindness towards yourself and others",
                "keywords": ["violence", "anger", "kindness", "peace", "harmony"]
            },
            {
                "concept": "Niyamas (Personal Observances)",
                "principle": "Santosha (Contentment)",
                "explanation": "Finding contentment in what you have",
                "application": "Practice gratitude and acceptance of present circumstances",
                "keywords": ["contentment", "gratitude", "acceptance", "peace", "satisfaction"]
            }
        ]
        
        self.ayurvedic_wisdom = [
            {
                "principle": "Dosha Balance",
                "concept": "Vata, Pitta, Kapha balance",
                "explanation": "Maintaining balance of bodily energies for mental health",
                "application": "Understand your nature and maintain balance through lifestyle",
                "keywords": ["balance", "energy", "nature", "lifestyle", "health"]
            },
            {
                "principle": "Sattva Guna",
                "concept": "Pure consciousness and clarity",
                "explanation": "Cultivating clarity and purity of mind",
                "application": "Engage in activities that promote mental clarity and peace",
                "keywords": ["clarity", "purity", "consciousness", "mind", "peace"]
            }
        ]
        
        self.buddhist_wisdom = [
            {
                "teaching": "Four Noble Truths",
                "principle": "Suffering exists, but there is a path to end it",
                "explanation": "Understanding the nature of suffering and liberation",
                "application": "Accept that suffering is part of life, but you can find peace",
                "keywords": ["suffering", "pain", "acceptance", "liberation", "peace"]
            },
            {
                "teaching": "Eightfold Path",
                "principle": "Right understanding leads to right action",
                "explanation": "Ethical living and mental discipline",
                "application": "Live ethically and develop mental discipline for inner peace",
                "keywords": ["ethics", "discipline", "understanding", "action", "peace"]
            }
        ]
        
        self.modern_psychology = [
            {
                "concept": "Cognitive Behavioral Therapy",
                "principle": "Thoughts affect emotions and behavior",
                "explanation": "Changing negative thought patterns improves mental health",
                "application": "Challenge negative thoughts and replace them with positive ones",
                "keywords": ["thoughts", "negative", "positive", "behavior", "emotions"]
            },
            {
                "concept": "Mindfulness",
                "principle": "Present moment awareness",
                "explanation": "Being fully present reduces anxiety and stress",
                "application": "Practice mindfulness meditation and present-moment awareness",
                "keywords": ["mindfulness", "present", "meditation", "anxiety", "stress"]
            }
        ]

        # Mental health resources
        self.mental_health_resources = {
            "crisis": {
                "india": [
                    "AASRA: +91-22-27546669 (24/7 suicide prevention)",
                    "Sneha India: +91-44-24640050 (24/7 emotional support)",
                    "iCall: 9152987821 (Mon-Sat, 8 AM-10 PM)"
                ],
                "international": [
                    "Crisis Text Line: Text HOME to 741741",
                    "International Association for Suicide Prevention: https://www.iasp.info/resources/Crisis_Centres/"
                ]
            },
            "therapy": {
                "online": [
                    "YourDOST: Professional counseling for Indians",
                    "BetterHelp: International online therapy",
                    "Manastha: Indian mental health platform"
                ],
                "helplines": [
                    "Vandrevala Foundation: 1860-266-2345",
                    "Mann Talks: +91-8686139139"
                ]
            }
        }

    def get_gita_wisdom(self, context=""):
        """Get most relevant Bhagavad Gita wisdom based on context"""
        context_lower = context.lower()
        
        # Find the most relevant shloka based on keywords
        for quote in self.gita_quotes:
            if any(keyword in context_lower for keyword in quote["keywords"]):
                return quote
        
        # If no specific match, return a random one
        return random.choice(self.gita_quotes)

    def get_inspire_wisdom(self, context=""):
        """Get inspiration insights from Indian personalities"""
        if "dream" in context.lower() or "goal" in context.lower():
            return self.inspire_quotes[0]
        elif "give up" in context.lower() or "quit" in context.lower():
            return self.inspire_quotes[1]
        else:
            return random.choice(self.inspire_quotes)

    def get_epic_story(self, context=""):
        """Get relevant story from Indian epics"""
        if "focus" in context.lower() or "concentrate" in context.lower():
            return self.epic_stories[0]
        elif "confidence" in context.lower() or "strength" in context.lower():
            return self.epic_stories[1]
        else:
            return random.choice(self.epic_stories)

    def smart_dataset_selection(self, user_input, mode="normal"):
        """Intelligently select the most appropriate dataset based on user input and context"""
        context_lower = user_input.lower()
        
        # Define dataset priorities and keywords
        dataset_keywords = {
            "gita": {
                "keywords": ["karma", "dharma", "duty", "action", "detachment", "gita", "krishna", "arjuna", "battle", "warrior", "spiritual", "soul", "atman"],
                "priority": 1,
                "dataset": self.gita_quotes,
                "method": self.get_gita_wisdom
            },
            "vedic": {
                "keywords": ["veda", "vedic", "ancient", "wisdom", "learning", "knowledge", "compassion", "universal", "noble", "thoughts"],
                "priority": 2,
                "dataset": self.vedic_wisdom,
                "method": self.get_vedic_wisdom
            },
            "yoga": {
                "keywords": ["yoga", "yamas", "niyamas", "ahimsa", "contentment", "ethics", "discipline", "balance", "harmony", "peace"],
                "priority": 3,
                "dataset": self.yoga_philosophy,
                "method": self.get_yoga_wisdom
            },
            "ayurvedic": {
                "keywords": ["ayurveda", "dosha", "vata", "pitta", "kapha", "balance", "energy", "nature", "lifestyle", "health", "body", "mind"],
                "priority": 4,
                "dataset": self.ayurvedic_wisdom,
                "method": self.get_ayurvedic_wisdom
            },
            "buddhist": {
                "keywords": ["buddha", "buddhist", "suffering", "pain", "acceptance", "liberation", "eightfold", "noble truths", "meditation", "mindfulness"],
                "priority": 5,
                "dataset": self.buddhist_wisdom,
                "method": self.get_buddhist_wisdom
            },
            "psychology": {
                "keywords": ["therapy", "cbt", "cognitive", "behavioral", "mindfulness", "anxiety", "depression", "stress", "emotions", "thoughts", "modern"],
                "priority": 6,
                "dataset": self.modern_psychology,
                "method": self.get_psychology_wisdom
            },
            "inspire": {
                "keywords": ["motivation", "inspiration", "success", "dream", "goal", "achieve", "leader", "kalam", "gandhi", "vivekananda"],
                "priority": 7,
                "dataset": self.inspire_quotes,
                "method": self.get_inspire_wisdom
            },
            "epic": {
                "keywords": ["mahabharata", "ramayana", "upanishad", "story", "epic", "focus", "concentration", "confidence", "strength", "lesson"],
                "priority": 8,
                "dataset": self.epic_stories,
                "method": self.get_epic_story
            }
        }
        
        # Score each dataset based on keyword matches
        dataset_scores = {}
        for dataset_name, config in dataset_keywords.items():
            score = 0
            for keyword in config["keywords"]:
                if keyword in context_lower:
                    score += 1
            dataset_scores[dataset_name] = {
                "score": score,
                "priority": config["priority"],
                "config": config
            }
        
        # If mode is explicitly set, prioritize that dataset
        if mode == "gita" and dataset_scores["gita"]["score"] > 0:
            return dataset_scores["gita"]["config"]["method"](user_input)
        elif mode == "inspire" and dataset_scores["inspire"]["score"] > 0:
            return dataset_scores["inspire"]["config"]["method"](user_input)
        
        # Find the best matching dataset
        best_dataset = None
        best_score = 0
        best_priority = float('inf')
        
        for dataset_name, data in dataset_scores.items():
            if data["score"] > best_score or (data["score"] == best_score and data["priority"] < best_priority):
                best_score = data["score"]
                best_priority = data["priority"]
                best_dataset = data["config"]
        
        # If no specific match found, use default based on mode
        if best_score == 0:
            if mode == "gita":
                return self.get_gita_wisdom(user_input)
            elif mode == "inspire":
                return self.get_inspire_wisdom(user_input)
            else:
                return self.get_gita_wisdom(user_input)  # Default to Gita
        
        return best_dataset["method"](user_input)

    def get_vedic_wisdom(self, context=""):
        """Get Vedic wisdom based on context"""
        context_lower = context.lower()
        for wisdom in self.vedic_wisdom:
            if any(keyword in context_lower for keyword in wisdom["keywords"]):
                return wisdom
        return random.choice(self.vedic_wisdom)

    def get_yoga_wisdom(self, context=""):
        """Get Yoga philosophy wisdom based on context"""
        context_lower = context.lower()
        for wisdom in self.yoga_philosophy:
            if any(keyword in context_lower for keyword in wisdom["keywords"]):
                return wisdom
        return random.choice(self.yoga_philosophy)

    def get_ayurvedic_wisdom(self, context=""):
        """Get Ayurvedic wisdom based on context"""
        context_lower = context.lower()
        for wisdom in self.ayurvedic_wisdom:
            if any(keyword in context_lower for keyword in wisdom["keywords"]):
                return wisdom
        return random.choice(self.ayurvedic_wisdom)

    def get_buddhist_wisdom(self, context=""):
        """Get Buddhist wisdom based on context"""
        context_lower = context.lower()
        for wisdom in self.buddhist_wisdom:
            if any(keyword in context_lower for keyword in wisdom["keywords"]):
                return wisdom
        return random.choice(self.buddhist_wisdom)

    def get_psychology_wisdom(self, context=""):
        """Get modern psychology wisdom based on context"""
        context_lower = context.lower()
        for wisdom in self.modern_psychology:
            if any(keyword in context_lower for keyword in wisdom["keywords"]):
                return wisdom
        return random.choice(self.modern_psychology)

    def detect_mood(self, user_input):
        """Simple mood detection based on keywords"""
        user_input = user_input.lower()
        
        if any(word in user_input for word in ["stressed", "anxious", "overwhelmed", "pressure"]):
            return "stressed"
        elif any(word in user_input for word in ["sad", "depressed", "down", "crying", "hurt"]):
            return "sad"
        elif any(word in user_input for word in ["motivated", "excited", "inspired", "energetic"]):
            return "motivated"
        elif any(word in user_input for word in ["calm", "peaceful", "meditate", "relax"]):
            return "peaceful"
        else:
            return "neutral"

    def assess_crisis_level(self, user_input):
        """Assess if user needs immediate mental health intervention"""
        crisis_keywords = [
            "suicide", "kill myself", "end it all", "no point living", 
            "want to die", "hurt myself", "self harm", "overdose"
        ]
        
        return any(keyword in user_input.lower() for keyword in crisis_keywords)

    def is_simple_greeting(self, user_input):
        """Check if input is a simple greeting"""
        simple_greetings = [
            "hi", "hello", "hey", "good morning", "good evening", "good afternoon",
            "namaste", "how are you", "what's up", "howdy", "greetings"
        ]
        return user_input.lower().strip() in simple_greetings
    

    def generate_response_by_mode(self, user_input, mode="normal", language="en"):
        """Generate appropriate response based on mode and input complexity"""
        try:
            mood = self.detect_mood(user_input)
            is_crisis = self.assess_crisis_level(user_input)
            
            # Crisis always gets immediate help regardless of mode
            if is_crisis:
                crisis_responses = {
                    "en": "🚨 I'm concerned about you. Please reach out immediately:\n• AASRA: +91-22-27546669\n• Sneha: +91-44-24640050\n• Emergency: 112\n\nYou're not alone. Help is available.",
                    "hi": "🚨 मैं आपकी चिंता कर रहा हूं। कृपया तुरंत संपर्क करें:\n• आसरा: +91-22-27546669\n• स्नेहा: +91-44-24640050\n• आपातकाल: 112\n\nआप अकेले नहीं हैं। मदद उपलब्ध है।",
                    "fr": "🚨 Je m'inquiète pour vous. Veuillez contacter immédiatement:\n• AASRA: +91-22-27546669\n• Sneha: +91-44-24640050\n• Urgence: 112\n\nVous n'êtes pas seul. L'aide est disponible.",
                    "es": "🚨 Me preocupo por ti. Por favor contacta inmediatamente:\n• AASRA: +91-22-27546669\n• Sneha: +91-44-24640050\n• Emergencia: 112\n\nNo estás solo. La ayuda está disponible.",
                    "ta": "🚨 நான் உங்களைப் பற்றி கவலைப்படுகிறேன். தயவுசெய்து உடனடியாக தொடர்பு கொள்ளுங்கள்:\n• ஆஸ்ரா: +91-22-27546669\n• ஸ்நேஹா: +91-44-24640050\n• அவசரகாலம்: 112\n\nநீங்கள் தனியாக இல்லை. உதவி கிடைக்கிறது.",
                    "te": "🚨 నేను మీ గురించి ఆందోళన చెందుతున్నాను. దయచేసి వెంటనే సంప్రదించండి:\n• ఆస్రా: +91-22-27546669\n• స్నేహ: +91-44-24640050\n• అత్యవసరం: 112\n\nమీరు ఒంటరిగా లేరు. సహాయం అందుబాటులో ఉంది.",
                    "pa": "🚨 ਮੈਂ ਤੁਹਾਡੇ ਬਾਰੇ ਚਿੰਤਤ ਹਾਂ। ਕਿਰਪਾ ਕਰਕੇ ਤੁਰੰਤ ਸੰਪਰਕ ਕਰੋ:\n• ਆਸਰਾ: +91-22-27546669\n• ਸਨੇਹਾ: +91-44-24640050\n• ਐਮਰਜੈਂਸੀ: 112\n\nਤੁਸੀਂ ਇਕੱਲੇ ਨਹੀਂ ਹੋ। ਮਦਦ ਉਪਲਬਧ ਹੈ।"
                }
                return {
                    "response": crisis_responses.get(language, crisis_responses["en"]),
                    "mood": mood,
                    "crisis_detected": True,
                    "timestamp": datetime.now().isoformat(),
                    "mode": mode,
                    "language": language
                }
            
            # Simple greetings get simple responses
            if self.is_simple_greeting(user_input):
                greeting_responses = {
                    "en": [
                        "Hello! I'm Sakha.ai 😊 How are you feeling today?",
                        "Hi there! 👋 I'm here to support you. What's on your mind?",
                        "Namaste! 🙏 I'm your wellness companion. How can I help?",
                        "Hey! 💜 Good to see you. How's your day going?"
                    ],
                    "hi": [
                        "नमस्ते! मैं Sakha.ai हूं 😊 आज आप कैसा महसूस कर रहे हैं?",
                        "हैलो! 👋 मैं आपका समर्थन करने के लिए यहां हूं। आपके मन में क्या है?",
                        "नमस्ते! 🙏 मैं आपका कल्याण साथी हूं। मैं कैसे मदद कर सकता हूं?",
                        "अरे! 💜 आपको देखकर अच्छा लगा। आपका दिन कैसा चल रहा है?"
                    ],
                    "fr": [
                        "Bonjour! Je suis Sakha.ai 😊 Comment vous sentez-vous aujourd'hui?",
                        "Salut! 👋 Je suis là pour vous soutenir. Qu'est-ce qui vous préoccupe?",
                        "Namaste! 🙏 Je suis votre compagnon de bien-être. Comment puis-je vous aider?",
                        "Hey! 💜 Ravi de vous voir. Comment se passe votre journée?"
                    ],
                    "es": [
                        "¡Hola! Soy Sakha.ai 😊 ¿Cómo te sientes hoy?",
                        "¡Hola! 👋 Estoy aquí para apoyarte. ¿Qué tienes en mente?",
                        "¡Namaste! 🙏 Soy tu compañero de bienestar. ¿Cómo puedo ayudarte?",
                        "¡Hey! 💜 Me alegra verte. ¿Cómo va tu día?"
                    ],
                    "ta": [
                        "வணக்கம்! நான் Sakha.ai 😊 இன்று நீங்கள் எப்படி உணருகிறீர்கள்?",
                        "வணக்கம்! 👋 நான் உங்களை ஆதரிக்க இங்கே இருக்கிறேன். உங்கள் மனதில் என்ன இருக்கிறது?",
                        "நமஸ்காரம்! 🙏 நான் உங்கள் நல்வாழ்வு துணை. நான் எப்படி உதவ முடியும்?",
                        "ஹே! 💜 உங்களைப் பார்த்து மகிழ்ச்சி. உங்கள் நாள் எப்படி போகிறது?"
                    ],
                    "te": [
                        "హలో! నేను Sakha.ai 😊 మీరు ఈరోజు ఎలా ఉన్నారు?",
                        "హలో! 👋 నేను మిమ్మల్ని మద్దతు ఇవ్వడానికి ఇక్కడ ఉన్నాను. మీ మనసులో ఏమి ఉంది?",
                        "నమస్కారం! 🙏 నేను మీ క్షేమ సహచరుడిని. నేను ఎలా సహాయపడగలను?",
                        "హే! 💜 మిమ్మల్ని చూసి సంతోషం. మీ రోజు ఎలా గడుస్తోంది?"
                    ],
                    "pa": [
                        "ਸਤ ਸ੍ਰੀ ਅਕਾਲ! ਮੈਂ Sakha.ai ਹਾਂ 😊 ਅੱਜ ਤੁਸੀਂ ਕਿਵੇਂ ਮਹਿਸੂਸ ਕਰ ਰਹੇ ਹੋ?",
                        "ਹੈਲੋ! 👋 ਮੈਂ ਤੁਹਾਡਾ ਸਮਰਥਨ ਕਰਨ ਲਈ ਇੱਥੇ ਹਾਂ। ਤੁਹਾਡੇ ਮਨ ਵਿੱਚ ਕੀ ਹੈ?",
                        "ਨਮਸਕਾਰ! 🙏 ਮੈਂ ਤੁਹਾਡਾ ਤੰਦਰੁਸਤੀ ਸਾਥੀ ਹਾਂ। ਮੈਂ ਕਿਵੇਂ ਮਦਦ ਕਰ ਸਕਦਾ ਹਾਂ?",
                        "ਹੇ! 💜 ਤੁਹਾਨੂੰ ਵੇਖ ਕੇ ਖੁਸ਼ੀ ਹੋਈ। ਤੁਹਾਡਾ ਦਿਨ ਕਿਵੇਂ ਗੁਜਰ ਰਿਹਾ ਹੈ?"
                    ]
                }
                responses = greeting_responses.get(language, greeting_responses["en"])
                return {
                    "response": random.choice(responses),
                    "mood": "neutral",
                    "crisis_detected": False,
                    "timestamp": datetime.now().isoformat(),
                    "mode": mode,
                    "language": language
                }
            
            # Mode-specific responses
            if mode == "gita":
                return self.generate_gita_response(user_input, mood, language)
            elif mode == "inspire":
                return self.generate_inspire_response(user_input, mood, language)
            else:  # normal mode
                return self.generate_normal_response(user_input, mood, language)
                
        except Exception as e:
            error_responses = {
                "en": "I'm here for you, though I'm having some technical difficulties. Please try again.",
                "hi": "मैं आपके लिए यहां हूं, हालांकि मुझे कुछ तकनीकी कठिनाइयों का सामना करना पड़ रहा है। कृपया फिर से कोशिश करें।",
                "ta": "நான் உங்களுக்காக இங்கே இருக்கிறேன், இருப்பினும் எனக்கு சில தொழில்நுட்ப சிக்கல்கள் உள்ளன. தயவுசெய்து மீண்டும் முயற்சிக்கவும்.",
                "te": "నేను మీ కోసం ఇక్కడ ఉన్నాను, అయితే నాకు కొన్ని సాంకేతిక ఇబ్బందులు ఉన్నాయి. దయచేసి మళ్లీ ప్రయత్నించండి.",
                "pa": "ਮੈਂ ਤੁਹਾਡੇ ਲਈ ਇੱਥੇ ਹਾਂ, ਹਾਲਾਂਕਿ ਮੈਨੂੰ ਕੁਝ ਤਕਨੀਕੀ ਮੁਸ਼ਕਲਾਂ ਆ ਰਹੀਆਂ ਹਨ। ਕਿਰਪਾ ਕਰਕੇ ਦੁਬਾਰਾ ਕੋਸ਼ਿਸ਼ ਕਰੋ।",
                "fr": "Je suis là pour vous, bien que j'aie quelques difficultés techniques. Veuillez réessayer.",
                "es": "Estoy aquí para ti, aunque tengo algunas dificultades técnicas. Por favor intenta de nuevo."
            }
            return {
                "response": error_responses.get(language, error_responses["en"]),
                "mood": "neutral",
                "crisis_detected": False,
                "timestamp": datetime.now().isoformat(),
                "mode": mode,
                "language": language
            }

    def generate_gita_response(self, user_input, mood, language="en"):
        """Generate wisdom-focused response using smart dataset selection"""
        wisdom = self.smart_dataset_selection(user_input, "gita")
        
        # Determine the wisdom type and format accordingly
        if "shloka" in wisdom:
            # Gita wisdom
            response_templates = {
                "en": f"""📖 **Bhagavad Gita Wisdom:**

*{wisdom['shloka']}*

**Translation:** {wisdom['translation']}

**Context:** {wisdom['context']}

**What this means:** {wisdom['practical_meaning']}

**Apply this:** {wisdom['life_application']}

🙏 May this ancient wisdom guide your path.""",
                "hi": f"""📖 **भगवद गीता का ज्ञान:**

*{wisdom['shloka']}*

**अनुवाद:** {wisdom['translation']}

**संदर्भ:** {wisdom['context']}

**इसका मतलब:** {wisdom['practical_meaning']}

**इसे लागू करें:** {wisdom['life_application']}

🙏 यह प्राचीन ज्ञान आपके मार्गदर्शन में सहायक हो।""",
                "ta": f"""📖 **பகவத் கீதை ஞானம்:**

*{wisdom['shloka']}*

**மொழிபெயர்ப்பு:** {wisdom['translation']}

**சூழல்:** {wisdom['context']}

**இதன் அர்த்தம்:** {wisdom['practical_meaning']}

**இதைப் பயன்படுத்துங்கள்:** {wisdom['life_application']}

🙏 இந்த பண்டைய ஞானம் உங்கள் பாதையை வழிநடத்தட்டும்।""",
                "te": f"""📖 **భగవద్ గీతా జ్ఞానం:**

*{wisdom['shloka']}*

**అనువాదం:** {wisdom['translation']}

**సందర్భం:** {wisdom['context']}

**దీని అర్థం:** {wisdom['practical_meaning']}

**దీన్ని వర్తింపజేయండి:** {wisdom['life_application']}

🙏 ఈ పురాతన జ్ఞానం మీ మార్గాన్ని నడిపించనివ్వండి।""",
                "pa": f"""📖 **ਭਗਵਦ ਗੀਤਾ ਦਾ ਗਿਆਨ:**

*{wisdom['shloka']}*

**ਅਨੁਵਾਦ:** {wisdom['translation']}

**ਸੰਦਰਭ:** {wisdom['context']}

**ਇਸਦਾ ਮਤਲਬ:** {wisdom['practical_meaning']}

**ਇਸਨੂੰ ਲਾਗੂ ਕਰੋ:** {wisdom['life_application']}

🙏 ਇਹ ਪੁਰਾਣਾ ਗਿਆਨ ਤੁਹਾਡੇ ਰਸਤੇ ਦੀ ਅਗਵਾਈ ਕਰੇ।""",
                "fr": f"""📖 **Sagesse de la Bhagavad Gita:**

*{wisdom['shloka']}*

**Traduction:** {wisdom['translation']}

**Contexte:** {wisdom['context']}

**Ce que cela signifie:** {wisdom['practical_meaning']}

**Appliquez ceci:** {wisdom['life_application']}

🙏 Que cette sagesse ancienne guide votre chemin.""",
                "es": f"""📖 **Sabiduría del Bhagavad Gita:**

*{wisdom['shloka']}*

**Traducción:** {wisdom['translation']}

**Contexto:** {wisdom['context']}

**Lo que esto significa:** {wisdom['practical_meaning']}

**Aplica esto:** {wisdom['life_application']}

🙏 Que esta sabiduría antigua guíe tu camino."""
            }
        elif "source" in wisdom:
            # Vedic wisdom
            response_templates = {
                "en": f"""📚 **{wisdom['source']} Wisdom:**

*"{wisdom['quote']}"*

**Context:** {wisdom['context']}

**Lesson:** {wisdom['lesson']}

🙏 Ancient wisdom for modern challenges.""",
                "hi": f"""📚 **{wisdom['source']} ज्ञान:**

*"{wisdom['quote']}"*

**संदर्भ:** {wisdom['context']}

**सबक:** {wisdom['lesson']}

🙏 आधुनिक चुनौतियों के लिए प्राचीन ज्ञान।""",
                "ta": f"""📚 **{wisdom['source']} ஞானம்:**

*"{wisdom['quote']}"*

**சூழல்:** {wisdom['context']}

**பாடம்:** {wisdom['lesson']}

🙏 நவீன சவால்களுக்கான பண்டைய ஞானம்।""",
                "te": f"""📚 **{wisdom['source']} జ్ఞానం:**

*"{wisdom['quote']}"*

**సందర్భం:** {wisdom['context']}

**పాఠం:** {wisdom['lesson']}

🙏 ఆధునిక సవాళ్లకు పురాతన జ్ఞానం।""",
                "pa": f"""📚 **{wisdom['source']} ਗਿਆਨ:**

*"{wisdom['quote']}"*

**ਸੰਦਰਭ:** {wisdom['context']}

**ਸਬਕ:** {wisdom['lesson']}

🙏 ਆਧੁਨਿਕ ਚੁਣੌਤੀਆਂ ਲਈ ਪੁਰਾਣਾ ਗਿਆਨ।""",
                "fr": f"""📚 **Sagesse {wisdom['source']}:**

*"{wisdom['quote']}"*

**Contexte:** {wisdom['context']}

**Leçon:** {wisdom['lesson']}

🙏 Sagesse ancienne pour les défis modernes.""",
                "es": f"""📚 **Sabiduría {wisdom['source']}:**

*"{wisdom['quote']}"*

**Contexto:** {wisdom['context']}

**Lección:** {wisdom['lesson']}

🙏 Sabiduría antigua para desafíos modernos."""
            }
        else:
            # Other wisdom types (yoga, ayurvedic, buddhist, psychology)
            source_name = wisdom.get('concept', wisdom.get('principle', wisdom.get('teaching', 'Wisdom')))
            response_templates = {
                "en": f"""🧘 **{source_name}:**

**{wisdom.get('principle', wisdom.get('concept', wisdom.get('teaching', '')))}**

**Explanation:** {wisdom['explanation']}

**Application:** {wisdom['application']}

💡 Ancient wisdom for modern well-being.""",
                "hi": f"""🧘 **{source_name}:**

**{wisdom.get('principle', wisdom.get('concept', wisdom.get('teaching', '')))}**

**व्याख्या:** {wisdom['explanation']}

**अनुप्रयोग:** {wisdom['application']}

💡 आधुनिक कल्याण के लिए प्राचीन ज्ञान।""",
                "ta": f"""🧘 **{source_name}:**

**{wisdom.get('principle', wisdom.get('concept', wisdom.get('teaching', '')))}**

**விளக்கம்:** {wisdom['explanation']}

**பயன்பாடு:** {wisdom['application']}

💡 நவீன நல்வாழ்வுக்கான பண்டைய ஞானம்।""",
                "te": f"""🧘 **{source_name}:**

**{wisdom.get('principle', wisdom.get('concept', wisdom.get('teaching', '')))}**

**వివరణ:** {wisdom['explanation']}

**అనువర్తనం:** {wisdom['application']}

💡 ఆధునిక క్షేమం కోసం పురాతన జ్ఞానం।""",
                "pa": f"""🧘 **{source_name}:**

**{wisdom.get('principle', wisdom.get('concept', wisdom.get('teaching', '')))}**

**ਵਿਆਖਿਆ:** {wisdom['explanation']}

**ਅਨੁਪ੍ਰਯੋਗ:** {wisdom['application']}

💡 ਆਧੁਨਿਕ ਤੰਦਰੁਸਤੀ ਲਈ ਪੁਰਾਣਾ ਗਿਆਨ।""",
                "fr": f"""🧘 **{source_name}:**

**{wisdom.get('principle', wisdom.get('concept', wisdom.get('teaching', '')))}**

**Explication:** {wisdom['explanation']}

**Application:** {wisdom['application']}

💡 Sagesse ancienne pour le bien-être moderne.""",
                "es": f"""🧘 **{source_name}:**

**{wisdom.get('principle', wisdom.get('concept', wisdom.get('teaching', '')))}**

**Explicación:** {wisdom['explanation']}

**Aplicación:** {wisdom['application']}

💡 Sabiduría antigua para el bienestar moderno."""
            }
        
        return {
            "response": response_templates.get(language, response_templates["en"]),
            "mood": mood,
            "crisis_detected": False,
            "timestamp": datetime.now().isoformat(),
            "mode": "gita",
            "language": language
        }

    def generate_inspire_response(self, user_input, mood, language="en"):
        """Generate inspiration focused response using smart dataset selection"""
        wisdom = self.smart_dataset_selection(user_input, "inspire")

        response_templates = {
            "en": f"""🌟 **Inspiration:**

**{wisdom['person']}** said:
*"{wisdom['quote']}"*

**Lesson for you:** {wisdom['lesson']}

💪 You have the strength to overcome any challenge!""",
            "hi": f"""🌟 **प्रेरणा:**

**{wisdom['person']}** ने कहा:
*"{wisdom['quote']}"*

**आपके लिए सबक:** {wisdom['lesson']}

💪 आपमें किसी भी चुनौती पर काबू पाने की ताकत है!""",
            "ta": f"""🌟 **ஊக்கம்:**

**{wisdom['person']}** கூறினார்:
*"{wisdom['quote']}"*

**உங்களுக்கான பாடம்:** {wisdom['lesson']}

💪 எந்த சவாலையும் சமாளிக்க உங்களுக்கு வலிமை உள்ளது!""",
            "te": f"""🌟 **ప్రేరణ:**

**{wisdom['person']}** అన్నారు:
*"{wisdom['quote']}"*

**మీ కోసం పాఠం:** {wisdom['lesson']}

💪 ఏ సవాళ్లను అధిగమించడానికి మీకు శక్తి ఉంది!""",
            "pa": f"""🌟 **ਪ੍ਰੇਰਣਾ:**

**{wisdom['person']}** ਨੇ ਕਿਹਾ:
*"{wisdom['quote']}"*

**ਤੁਹਾਡੇ ਲਈ ਸਬਕ:** {wisdom['lesson']}

💪 ਤੁਹਾਡੇ ਵਿੱਚ ਕਿਸੇ ਵੀ ਚੁਣੌਤੀ 'ਤੇ ਕਾਬੂ ਪਾਉਣ ਦੀ ਤਾਕਤ ਹੈ!""",
            "fr": f"""🌟 **Inspiration:**

**{wisdom['person']}** a dit:
*"{wisdom['quote']}"*

**Leçon pour vous:** {wisdom['lesson']}

💪 Vous avez la force de surmonter n'importe quel défi!""",
            "es": f"""🌟 **Inspiración:**

**{wisdom['person']}** dijo:
*"{wisdom['quote']}"*

**Lección para ti:** {wisdom['lesson']}

💪 ¡Tienes la fuerza para superar cualquier desafío!"""
        }
        
        return {
            "response": response_templates.get(language, response_templates["en"]),
            "mood": mood,
            "crisis_detected": False,
            "timestamp": datetime.now().isoformat(),
            "mode": "inspire",
            "language": language
        }

    def generate_normal_response(self, user_input, mood, language="en"):
        """Generate response using only Google API"""
        # Get AI response if available
        if GOOGLE_API_KEY and model is not None:
            language_prompts = {
                "en": f"""You are Sakha.ai, a compassionate mental health and wellness companion. 
Respond to: "{user_input}"
                
Guidelines:
- Be warm, supportive, and empathetic
- Keep responses conversational and helpful
- Focus on mental health support and wellness
- Be encouraging but not preachy
- Use emojis sparingly and appropriately""",
                "hi": f"""आप Sakha.ai हैं, एक दयालु मानसिक स्वास्थ्य और कल्याण साथी।
इस पर प्रतिक्रिया दें: "{user_input}"
                
दिशानिर्देश:
- गर्म, सहायक और सहानुभूतिपूर्ण बनें
- बातचीत को सहायक और मददगार रखें
- मानसिक स्वास्थ्य सहायता और कल्याण पर ध्यान दें
- प्रोत्साहित करें लेकिन उपदेशात्मक न बनें
- इमोजी का कम उपयोग करें""",
                "fr": f"""Vous êtes Sakha.ai, un compagnon compatissant en santé mentale et bien-être.
Répondez à: "{user_input}"
                
Directives:
- Soyez chaleureux, solidaire et empathique
- Gardez les réponses conversationnelles et utiles
- Concentrez-vous sur le soutien en santé mentale et le bien-être
- Soyez encourageant mais pas moralisateur
- Utilisez les emojis avec parcimonie""",
                "es": f"""Eres Sakha.ai, un compañero compasivo de salud mental y bienestar.
Responde a: "{user_input}"
                
Pautas:
- Sé cálido, solidario y empático
- Mantén las respuestas conversacionales y útiles
- Enfócate en el apoyo de salud mental y bienestar
- Sé alentador pero no sermoneador
- Usa emojis con moderación""",
                "ta": f"""நீங்கள் Sakha.ai, ஒரு இரக்கமுள்ள மன ஆரோக்கிய மற்றும் நல்வாழ்வு துணை.
இதற்கு பதிலளிக்கவும்: "{user_input}"
                
வழிகாட்டுதல்கள்:
- வெப்பமாக, ஆதரவாக மற்றும் பச்சாதாபமாக இருங்கள்
- பேச்சுவழக்கு மற்றும் பயனுள்ள பதில்களை வைத்திருங்கள்
- மன ஆரோக்கிய ஆதரவு மற்றும் நல்வாழ்வில் கவனம் செலுத்துங்கள்
- ஊக்கமளிக்கவும் ஆனால் போதனை செய்யாதீர்கள்
- எமோஜிகளை மிதமாக பயன்படுத்துங்கள்""",
                "te": f"""మీరు Sakha.ai, ఒక దయగల మానసిక ఆరోగ్య మరియు క్షేమ సహచరుడు.
దీనికి సమాధానం ఇవ్వండి: "{user_input}"
                
మార్గదర్శకాలు:
- వెచ్చదనంతో, మద్దతుతో మరియు సానుభూతితో ఉండండి
- సంభాషణ మరియు ఉపయోగకరమైన సమాధానాలను ఉంచండి
- మానసిక ఆరోగ్య మద్దతు మరియు క్షేమంపై దృష్టి పెట్టండి
- ప్రోత్సాహించండి కానీ ఉపదేశం చేయకండి
- ఇమోజీలను మితంగా ఉపయోగించండి""",
                "pa": f"""ਤੁਸੀਂ Sakha.ai ਹੋ, ਇੱਕ ਦਿਆਲੂ ਮਾਨਸਿਕ ਸਿਹਤ ਅਤੇ ਤੰਦਰੁਸਤੀ ਸਾਥੀ।
ਇਸਦਾ ਜਵਾਬ ਦਿਓ: "{user_input}"
                
ਦਿਸ਼ਾਨਿਰਦੇਸ਼:
- ਗਰਮ, ਸਹਾਇਕ ਅਤੇ ਹਮਦਰਦੀ ਭਰਪੂਰ ਰਹੋ
- ਗੱਲਬਾਤ ਅਤੇ ਮਦਦਗਾਰ ਜਵਾਬ ਰੱਖੋ
- ਮਾਨਸਿਕ ਸਿਹਤ ਸਹਾਇਤਾ ਅਤੇ ਤੰਦਰੁਸਤੀ 'ਤੇ ਧਿਆਨ ਦਿਓ
- ਉਤਸ਼ਾਹਿਤ ਕਰੋ ਪਰ ਉਪਦੇਸ਼ ਨਾ ਦਿਓ
- ਇਮੋਜੀ ਦਾ ਮਿਤ ਵਰਤੋਂ ਕਰੋ"""
            }
            
            prompt = language_prompts.get(language, language_prompts["en"])
            
            try:
                response = model.generate_content(prompt)
                ai_response = response.text
                print(f"✅ API call successful: {ai_response[:50]}...")
            except Exception as e:
                print(f"❌ API call failed: {e}")
                print(f"❌ API Key present: {bool(GOOGLE_API_KEY)}")
                print(f"❌ Model configured: {model is not None}")
                fallback_responses = {
                    "en": "I'm here to support you through whatever you're going through. 💜",
                    "hi": "मैं आपके साथ हूं, चाहे आप कुछ भी कर रहे हों। 💜",
                    "ta": "நீங்கள் எதைச் செய்தாலும் நான் உங்களுடன் இருக்கிறேன்। 💜",
                    "te": "మీరు ఏమి చేస్తున్నా నేను మీతో ఉన్నాను। 💜",
                    "pa": "ਤੁਸੀਂ ਜੋ ਵੀ ਕਰ ਰਹੇ ਹੋ, ਮੈਂ ਤੁਹਾਡੇ ਨਾਲ ਹਾਂ। 💜",
                    "fr": "Je suis là pour vous soutenir dans tout ce que vous traversez. 💜",
                    "es": "Estoy aquí para apoyarte en lo que estés pasando. 💜"
                }
                ai_response = fallback_responses.get(language, fallback_responses["en"])
        else:
            fallback_responses = {
                "en": "I'm here to support you. 💜",
                "hi": "मैं आपका समर्थन करने के लिए यहां हूं। 💜",
                "ta": "நான் உங்களை ஆதரிக்க இங்கே இருக்கிறேன்। 💜",
                "te": "నేను మిమ్మల్ని మద్దతు ఇవ్వడానికి ఇక్కడ ఉన్నాను। 💜",
                "pa": "ਮੈਂ ਤੁਹਾਡਾ ਸਮਰਥਨ ਕਰਨ ਲਈ ਇੱਥੇ ਹਾਂ। 💜",
                "fr": "Je suis là pour vous soutenir. 💜",
                "es": "Estoy aquí para apoyarte. 💜"
            }
            ai_response = fallback_responses.get(language, fallback_responses["en"])
        
        return {
            "response": ai_response,
            "mood": mood,
            "crisis_detected": False,
            "timestamp": datetime.now().isoformat(),
            "mode": "normal",
            "language": language
        }

    def get_gentle_wisdom(self, user_input):
        """Fallback gentle response when main system has issues"""
        inspire = self.get_inspire_wisdom(user_input)
        return f"""
Even in difficult moments, remember:

📖 **From the Bhagavad Gita:**
    *{inspire['translation']}*

This reminds us: {inspire['relevance']}

🤗 Take a deep breath. You have the strength to get through this.
"""

# Initialize Sakha.ai
sakha = SakhaAI()

# API Routes
@app.get("/")
async def serve_frontend():
    """Serve the main frontend page"""
    return FileResponse("static/index.html")

@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(message: ChatMessage):
    """Main chat endpoint"""
    try:
        if not message.message.strip():
            default_responses = {
                "en": "Hi! I'm Sakha.ai, your compassionate companion. How are you feeling today?",
                "hi": "नमस्ते! मैं Sakha.ai हूं, आपका दयालु साथी। आज आप कैसा महसूस कर रहे हैं?",
                "ta": "வணக்கம்! நான் Sakha.ai, உங்கள் இரக்கமுள்ள துணை. இன்று நீங்கள் எப்படி உணருகிறீர்கள்?",
                "te": "హలో! నేను Sakha.ai, మీ దయగల సహచరుడిని. మీరు ఈరోజు ఎలా ఉన్నారు?",
                "pa": "ਸਤ ਸ੍ਰੀ ਅਕਾਲ! ਮੈਂ Sakha.ai ਹਾਂ, ਤੁਹਾਡਾ ਦਿਆਲੂ ਸਾਥੀ। ਅੱਜ ਤੁਸੀਂ ਕਿਵੇਂ ਮਹਿਸੂਸ ਕਰ ਰਹੇ ਹੋ?",
                "fr": "Salut! Je suis Sakha.ai, votre compagnon compatissant. Comment vous sentez-vous aujourd'hui?",
                "es": "¡Hola! Soy Sakha.ai, tu compañero compasivo. ¿Cómo te sientes hoy?"
            }
            return ChatResponse(
                response=default_responses.get(message.language, default_responses["en"]),
                mood="neutral",
                crisis_detected=False,
                timestamp=datetime.now().isoformat(),
                mode=message.mode,
                language=message.language
            )
        
        # Add to conversation history
        sakha.conversation_history.append({"user": message.message, "timestamp": datetime.now()})
        
        # Generate response based on mode
        response_data = sakha.generate_response_by_mode(message.message, message.mode, message.language)
        
        # Add bot response to history
        sakha.conversation_history.append({"bot": response_data["response"], "timestamp": datetime.now()})
        
        return ChatResponse(**response_data)
        
    except Exception as e:
        error_responses = {
            "en": "I'm experiencing some technical difficulties, but I'm still here for you. Please try again.",
            "hi": "मुझे कुछ तकनीकी कठिनाइयों का सामना करना पड़ रहा है, लेकिन मैं अभी भी आपके साथ हूं। कृपया फिर से कोशिश करें।",
            "ta": "நான் சில தொழில்நுட்ப சிக்கல்களை அனுபவிக்கிறேன், ஆனால் நான் இன்னும் உங்களுடன் இருக்கிறேன். தயவுசெய்து மீண்டும் முயற்சிக்கவும்.",
            "te": "నేను కొన్ని సాంకేతిక ఇబ్బందులను అనుభవిస్తున్నాను, కానీ నేను ఇంకా మీతో ఉన్నాను. దయచేసి మళ్లీ ప్రయత్నించండి.",
            "pa": "ਮੈਂ ਕੁਝ ਤਕਨੀਕੀ ਮੁਸ਼ਕਲਾਂ ਦਾ ਸਾਹਮਣਾ ਕਰ ਰਿਹਾ ਹਾਂ, ਪਰ ਮੈਂ ਅਜੇ ਵੀ ਤੁਹਾਡੇ ਨਾਲ ਹਾਂ। ਕਿਰਪਾ ਕਰਕੇ ਦੁਬਾਰਾ ਕੋਸ਼ਿਸ਼ ਕਰੋ।",
            "fr": "J'éprouve quelques difficultés techniques, mais je suis toujours là pour vous. Veuillez réessayer.",
            "es": "Estoy experimentando algunas dificultades técnicas, pero sigo aquí para ti. Por favor intenta de nuevo."
        }
        return ChatResponse(
            response=error_responses.get(message.language, error_responses["en"]),
            mood="neutral",
            crisis_detected=False,
            timestamp=datetime.now().isoformat(),
            mode=message.mode,
            language=message.language
        )


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "ai_enabled": model is not None,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/resources")
async def get_resources():
    """Get mental health resources"""
    return sakha.mental_health_resources

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Sakha.ai FastAPI server...")
    uvicorn.run(app, host="0.0.0.0", port=5000)