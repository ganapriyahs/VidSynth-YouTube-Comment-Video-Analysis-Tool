import json
import os
import sys
from dotenv import load_dotenv

from huggingface_hub import InferenceClient
from huggingface_hub import HfApi


def summarize_with_hf(text: string, type_summary: string) -> string:
    """
    text: is the input source transcript or total comment section
    type_summary: is a string to indicate whether the input is a transcript or comment section
    return: the summary generated
    """
    # Format your prompt
    if type_summary == "trans":
        messages = [
            {"role": "system", "content": "You are a helpful assistant that provides detailed summaries."},
            {"role": "user", "content": f"Please summarize the following YouTube video:\n\n{text}"}
        ]
    elif type_summary == "comments":
        messages = [
            {"role": "system", "content": "You are a helpful assistant that provides concise summaries."},
            {"role": "user", "content": f"Please summarize the following YouTube Comment Section:\n\n{text}"}
        ]
    else:
        print("Error: Invalid 'type_summary' passed '{type_summary}'")
        return None
    
    # Make inference call
    response = client.chat_completion(
        messages=messages,
        max_tokens=1500,
        temperature=0.3
    )
    
    return response.choices[0].message.content

# def process_text(text):
#     if isinstance(text, bytes):
#         text = text.decode('utf-8', errors='ignore')
    
#     # Clean the text
#     text = text.strip()
    
#     # Verify it's valid UTF-8
#     try:
#         text.encode('utf-8')
#     except UnicodeEncodeError as e:
#         print(f"Encoding error: {e}")
#         # Remove problematic characters
#         text = text.encode('utf-8', errors='ignore').decode('utf-8')
    
#     return text

# import unicodedata

# def clean_hindi_text(text):
#     # Remove zero-width characters
#     text = text.replace('\u200b', '')  # Zero-width space
#     text = text.replace('\u200c', '')  # Zero-width non-joiner
#     text = text.replace('\u200d', '')  # Zero-width joiner
#     text = text.replace('\ufeff', '')  # Zero-width no-break space
    
#     # Normalize Unicode
#     text = unicodedata.normalize('NFKC', text)
    
#     # Remove any control characters except newlines and tabs
#     cleaned = ''.join(char for char in text 
#                      if unicodedata.category(char)[0] != 'C' 
#                      or char in ['\n', '\t'])
    
#     return cleaned




if __name__ == "__main__":

    load_dotenv()

    # Load and store the API key as part of the environment (no need to pass api key later)
    api = HfApi(token=os.getenv("HF_TOKEN"))

    # Hugging Face inference API
    client = InferenceClient(
        #"meta-llama/Meta-Llama-3-8B-Instruct" # need 'instruct' version (instruction tuned for chat)
        "meta-llama/Llama-3.1-8B-Instruct"
        #api_key="api"
    )

    try:
        with open('videoList.json', 'r', encoding='utf-8') as f:
            videoListData = json.load(f)
    except FileNotFoundError:
        print("Error: Run 'initialize_validation_set. first'")
        sys.exit(1)

    # iterate over each video and generate summary for each transcript and comment section 
    for test in videoListData['videoList']:
        print(f"Attempting to generate summaries for {test['video_url']}")

        if test.get('trans_summary') is not None and test.get('comment_summary') is not None:
            print("Already processed, skipping this summary...")
            continue
        
        tempTrans = test['transcript']
        tempSummaryTrans = summarize_with_hf(tempTrans, type_summary="trans")
        # update the JSON file
        test['trans_summary'] = tempSummaryTrans
        print("Succesfully generated and wrote transcript summary")

        tempComments = "".join(test['comment_array'])
        tempSummaryComments = summarize_with_hf(tempComments, type_summary="comments")
        test['comment_summary'] = tempSummaryComments
        print("Succesfully generated and wrote comment section summary\n")

        # Save after each video in case of crashes
        with open('videoList.json', 'w', encoding='utf-8') as f:
            json.dump(videoListData, f, indent=2, ensure_ascii=False)
        



    # Example usage (Comment out above for loop)
    # inputTran = """[Music] here you are here [Music] people in the Eastern Democratic Republic of Congo have endured 25 years of war the conflict here is the deadliest global conflict since World War II with over 6 million people killed now they're facing down another Rebellion foreign [Applause] [Music] recruitment side in the last couple of weeks the president called for everybody to arm themselves or to join the Army in order to fight against the m-23 Rebels the general said that over a thousand people are showing up every day here to join the fight ice ice after Decades of violence and an explosion of Rebel groups looking to exploit its mineral resources the country is frantically mobilizing against the M23 Rebels militants from the minority Tootsie ethnic group who last took the regional Capital Goma in 2012. fighting between the Army and M23 has displaced over half a million Congolese people in just a few months the national Army along with the 15 000 strong U.N peacekeeping Force haven't been able to stop the rebels from taking critical territory determined to stop Goma from falling to the rebels again men and women across the East are joining the fight Esperance patende left her two children at home and traveled over 60 miles on foot to enlist [Music] [Music] Ed [Music] Esperance knows Congo's cyclical violence well her father and husband were both killed fighting in the army during the last M23 Rebellion did you feel like they died Heroes yeah foreign and who do you think is responsible specifically for this conflict Rwanda nirwanda but the rebels are Congolese right they've been fighting here before Congo's neighbors Rwanda and Uganda have fueled instability here for decades backing proxy militias in order to illegally extract minerals like Colton and gold Rwanda is the world's third largest coldhand exporter even though Rwanda has no industrial koltan mines Rwanda denies meddling in Congo but its supportive M23 was confirmed by a leaked un Report with photos of Rwandan troops Crossing into Congo and M23 Fighters with Rwandan army uniforms and weapons these links mean the conflict risks spiraling into a regional war that plays out along ethnic Alliance M23 was formed by ethnic tootsies the group targeted in rwanda's 1994 genocide and the ethnicity of rwanda's President Rwanda now claims that Congolese Tutsis are being harassed and killed in the name of fighting M23 in a country where Rebel groups form along ethnic loyalties the president's latest move could make things worse foreign the Eastern region of North kibu has borne the brunt of Rebel groups vying to control mineral wealth it's been under an official state of siege for almost two years and is now on the front line of m23's fight we're on the way to meet up with one of these vigilante groups that's fighting against M23 their former Rebels now recruiting again to join this fight it's been really complicated to negotiate a way to actually get to them because M23 is advancing and this is an area that's kind of littered with Rebel groups with Bandits and with a military presence so we've had to negotiate with a bunch of the different groups in order to try and guarantee safe Passage [Applause] foreign [Applause] when we arrived we drove straight into crowds gathered to celebrate the arrival of the rebels self-proclaimed Lieutenant General jean-vie carreri leads the alliance of Patriots for a free and Sovereign Congo or apcls Rebels and fought the M23 in 2012. [Applause] the general is welcomed here by people living just a few miles from advancing m-23 soldiers foreign [Applause] [Applause] [Music] [Applause] [Music] [Applause] civilians and rebels fighting with other groups foreign [Music] [Music] [Applause] to us right now how close is the threat foreign do you feel ready to with these new recruits to be in battle with them in the next few days and I see you're fighting alongside and for the same cause as the National military why is that after you've been on the other side in the past foreign [Applause] accusing M23 of being funded by Rwanda maybe even Uganda can you tell me where you get your funding she said so how are you managing to pay for all of these guys weapons comms equipment you have no one even local support foreign have you given any thought to what's going to happen after you defeat M23 what will happen to all of these different factions of Rebel groups and army foreign new Rebel coalitions the town fell to M23 just a few weeks later as the Army and rebel groups Scramble for new recruits M23 has vowed to continue their offensive to push the government into negotiating with them they claim they're protecting the tootsie minority in eastern Congo and accuse the government of not honoring their previous peace agreement after months of resisting media coverage raising suspicions that they're hiding Rwandan soldiers in their ranks are contacts with the group gave us 24 hours notice to meet them at their military headquarters to reach their territory we had to leave Congo the group then facilitated our entry through Rwanda and Uganda foreign so we're just crossing into Congo from Uganda and it's at a border post that's been closed for the last year because of the conflict here this is the first town that M23 took when they were going back into Congo when we got here at first they weren't going to let us cross they wouldn't let us take the car but it seems like they're letting us cross now [Music] foreign [Applause] evidence that M23 is massacring civilians the group's leaders finally agreed to talk to the Press ures killing me an important at a press conference to defend themselves against allegations by the UN about civilian deaths the group's political leader batra basimwa also insisted Congo's Tootsie population are facing a genocide is a [Music] foreign [Music] so I understand that you've said the Congolese government are the ones who started the war today at your press conference you also denied any responsibility for these massacres that the UN said killed at least 170 people are you at any point going to take some responsibility for the impact of the war here is foreign you have used the word genocide a lot that's a very inflammatory word to use here sitting on the border of Rwanda and Congo and there's no evidence yet that the discrimination against the tootsie Congolese population is anywhere close to a genocide at the current moment foreign the wonderful exterminations do you categorically deny like the other leaders of M23 that you have any backing Financial or logistical from Rwanda or Uganda but you could have the support of Rwanda and Uganda without having the full support of their armies there's U.N group of experts reports eyewitness accounts of Rwandan forces on the ground reports of funding and logistical support do you deny all of that after pushing him on Rwanda our interview was cut short and we were asked to leave the country earlier than planned so these m-23 soldiers are just escorting us back to the Ugandan border that we crossed this morning we're not entirely sure why it's such a rush originally they told us we could stay a bit longer but they suddenly said that we had to go Rwandan authorities denied a repeated request for an interview but told Vice news quote Rwanda has no interest in perpetuating a conflict on its borders or being drawn into an internal conflict in the DRC adding the accusations of the UN group of experts are without basis even in the face of an international war with Rwanda Congo's government has much more than M23 to contend with it the population's anger is boiling over into sustained protests against the perceived failure of the government and the U.N to protect people [Music] the un's menusco peacekeeping mission is one of the largest and oldest in the world it has a billion dollar annual budget and peacekeepers and bases across the country but resentment against the blue helmets has been building for years as poorly armed Rebels continue to Massacre civilians in towns with large UN forces [Music] organizers like Jackson Zahara are behind the protests demanding for the UN to leave the country is rallying participants for another protest to demand that foreign troops the U.N and Regional forces from East Africa leave Congo to fight its own battles why is there such intense anger even when this population is being attacked by Rebel groups in their area why are they so angry at the U.N color is [Music] no job business so you don't think it would have any impact if all these troops all of these weapons that are supposed to protect people here just disappeared tomorrow existed Continental foreign [Music] [Music] anti-un protests have turned deadly at least 29 civilians and four U.N peacekeepers died in protests where U.N facilities were ransacked and looted throughout Eastern Congo [Music] despite the risks people still turned up in downtown Goma to join since Sahara's team these protesters are trying to make it to the center of the city outside one of the big U.N peacekeeping bases there but the police the governor and the U.N have all asked them to call it off already [Music] so it looks like about a quarter of the protesters actually made it here to the U.N the police stopped a bunch of them in town they arrested some journalists these guys at least are going to try and do a sit-in here [Music] but as soon as police descended the remaining protesters had to run M23 has surrounded Goma and vows to take the city again frustrated and Angry Young Congolese people like Esperance say this fight is the last straw in the endless violence they've experienced do you think in your lifetime that Eastern Congo can be totally at peace and rid of all of these Rebel groups [Music] I'm Michael lermont editor-in-chief of Vice news too often traditional news outlets shy away from the real stories and experiences of those living through Global conflicts not Vice news our reporters are on the ground fearlessly covering the human stories that shape our world you and millions of others can continue to read watch and listen to Vice news for free but we hope you'll consider making a one-time or ongoing contribution of any size advice.com contribute every contribution no matter how big or small helps support the journalism Vice news brings to you every day thank you
    # """
    # inputTran_H = """"नमस्कार, दिनभर की बड़ी खबरों में आपका स्वागत है। मैं हूं आंचल। आज इस बुलेटिन में बात होगी नीतीश कुमार को लगे बड़े झटके की। बीजेपी नेता के बयान से पार्टी की बढ़ती मुश्किलों की। देखेंगे एसआईआर को लेकर चुनाव आयोग पर बढ़ते दबाव को। अखिलेश यादव ने एनडीए को दी क्या नसीहत। जानेंगे मोदी सरकार पर क्यों भड़का आरएसएस? और बुलेटिन के आखिर में देखेंगे जानेमाने कार्टूनिस्ट इरफान की किस खबर पर पड़ी तिरछी नजर। लेकिन दिनभर की तमाम बड़ी खबरों से पहले एक नजर आज की सुर्खियों पर। दुबई एयर शो में हुआ बड़ा हादसा। भारतीय फाइटर जेट तेजस हुआ क्रैश। पायलट की गई जान। संसद के शीतकालीन सत्र से पहले सरकार ने बुलाई सर्वदलीय बैठक। 30 नवंबर को सुबह 11:00 बजे होगी बैठक। 1 दिसंबर से 19 दिसंबर तक चलेगा शीतकालीन सत्र। सीजीआई बिहार गवाई का बड़ा बयान। कहा बौद्ध धर्म को मानने वाला लेकिन सेकुलर हूं। 23 नवंबर को रिटायर हो रहे हैं सीजीआई गवाई। और शेयर बाजार में गिरावट। 400 अंकों की गिरावट के साथ 85,231 पर बंद हुआ सेंसेक्स। तो, 124 अंकों की गिरावट के साथ 26,68 पर बंद हुआ निफ़ी। यह तो थी सुर्खियां। अब बात आज की सबसे बड़ी खबर की। बिहार में नीतीश सरकार में मंत्रियों के बीच विभागों का बंटवारा हो गया है और इस बंटवारे में भी नीतीश की ज्यादा चलती नहीं दिखाई दी। जेडीयू की सीटें भले ही बढ़ गई हो लेकिन नीतीश कुमार इस बार कमजोर पड़ते दिखाई दे रहे हैं। 20 साल से जिस विभाग को लेकर नीतीश कुमार हमेशा सहयोगियों के सामने अड़ जाते थे। इस बार बीजेपी के पाले में वह विभाग भी चला गया। तो कैसे कमजोर पड़ते दिखाई दे रहे हैं नीतीश जानने के लिए देखिए रिपोर्ट। नीतीश कुमार 2005 में बिहार के सीएम बने और उन्होंने गृह मंत्रालय भी अपने ही पास रखा। 2025 में हुए विधानसभा चुनाव तक गृह मंत्रालय जेडीयू के पास ही रहा और इसमें भी 19 साल तो नीतीश कुमार ही गृह मंत्री रहे। बीजेपी ने कई बार नीतीश से गृह मंत्रालय मांगा लेकिन हर बार उन्होंने बीजेपी हाईकमान को यह मंत्रालय देने से इंकार कर दिया। लेकिन इस बार नीतीश कुमार बीजेपी के सामने सरेंडर करते दिखाई दिए हैं। गृह मंत्रालय इस बार बीजेपी के सम्राट चौधरी को दिया गया है। वैसे बदले में बीजेपी के हिस्से में रहने वाला वित्त मंत्रालय नीतीश ने जेडीयू के लिए झटक लिया। जेडीयू के विजेंद्र यादव को वित्त विभाग मिला। इसके अलावा उन्हें वाणिज्य और ऊर्जा मंत्रालय भी दिया गया है। बीजेपी के नितिन नवीन को पीडब्ल्यूडी के साथ शहरी विकास और आवास मंत्रालय दिया गया है। बीजेपी के प्रदेश अध्यक्ष दिलीप जायसवाल को उद्योग मंत्री विजय सिन्हा को भूमि और राजस्व के साथ खनन और भूतत्व मंत्रालय दिया गया है। जेडीयू के श्रवण कुमार को ग्रामीण विकास कार्य और परिवहन मंत्री बनाया गया है। यानी एक बात तो साफ हो गई है कि मंत्रालय के बंटवारे में बीजेपी का दबदबा दिखाई दिया। ऐसे में अब सभी की निगाहें विधानसभा अध्यक्ष पद को लेकर हैं कि क्या यह पद भी बीजेपी के हिस्से में चला जाएगा। वैसे जिन मंत्रियों को महत्वपूर्ण मंत्रालय सौंपे गए हैं, उसे लेकर भी सवाल उठ रहे हैं। खासतौर पर जिस तरह से नीतीश सरकार में परिवारवाद का दबदबा दिखाई दिया है, उसे लेकर आरजेडी ने सवाल उठाए हैं। नीतीश सरकार में डिप्टी सीएम सहित तमाम बड़े मंत्री किसी ना किसी सियासी खानदान से जुड़े हुए हैं। जिसमें डिप्टी सीएम सम्राट चौधरी का नाम भी शामिल है। ऐसे में विपक्ष ने नीतीश सरकार को घेर लिया है जो विपक्ष पर परिवारवाद का आरोप लगाते रहे हैं। नीतीश कुमार को बीजेपी ने बड़ा झटका दे दिया है। तो मुश्किलों में बीजेपी भी दिखाई दे रही है। बिहार चुनाव में विपक्ष बीजेपी पर रिश्वतखोरी का आरोप लगा रहा था और अब बीजेपी के नेता ने ही विपक्ष के आरोपों पर मोहर लगा दी है। बीजेपी के उस नेता ने जिसने नरेंद्र मोदी के लिए अपनी सीट छोड़ी थी। उसने ऐसा बयान दिया है जिसकी चर्चा जोरों पर है तो कौन है वह नेता और क्या कुछ कहा उन्होंने जानने के लिए देखिए यह रिपोर्ट। 14 नवंबर को बिहार की बाजी एनडीए ने जीत ली। 20 नवंबर को जेडीयू नेता नीतीश कुमार ने 10वीं बार सीएम पद की शपथ ली। लेकिन इन सबके बीच विपक्ष एक मुद्दे को लेकर बीजेपी पर भड़का हुआ है और वह मुद्दा है रिश्वतखोरी का। दरअसल बिहार चुनाव से पहले बीजेपी ने मुख्यमंत्री महिला सम्मान योजना की शुरुआत की थी जिसके तहत हर महिला के खाते में ₹10,000 ट्रांसफर किए जा रहे थे। इस योजना का विपक्ष ने जमकर विरोध किया और इसे चुनाव से पहले रिश्वतखोरी करार दिया। अब खास बात यह है कि विपक्ष के बाद अब बीजेपी के वरिष्ठ नेता मुरली मनोहर जोशी ने चुनाव से पहले पैसे बांटने को लेकर एनडीए पर तंज कसा है। उन्होंने कहा कि विकास का अर्थ चुनावों में पैसे बांटना नहीं है। देश में आर्थिक असमानता ही सबसे बड़ा भेदभाव बन चुकी है। कल्याणकारी कार्य चुनावों में पैसा बांटने से नहीं होते हैं। आज लोग सवाल उठाते हैं कि चुनाव से पहले कैश बांटा जा रहा है। सरकार कहती है कि ऐसा वेलफेयर के लिए किया जा रहा है। लेकिन लोग कहते हैं कि आप वोट खरीदने के लिए पैसे बांटते हैं। बता दें कि मुरली मनोहर जोशी का यह बयान ऐसे समय में आया है जब बिहार चुनाव के नतीजों को लेकर सियासत में घमासान मचा हुआ है। विपक्ष लगातार नतीजों में धांधली के आरोप लगा रहा है और नतीजों की समीक्षा करने की चेतावनी भी दे रहा है। इस बीच अब देखना यह होगा कि बीजेपी अपने ही नेता के दिए हुए बयान पर क्या सफाई देती है। बीजेपी नेता के बयान से पूरा एनडीए फंसता दिखाई दे रहा है। तो एसआईआर को लेकर चुनाव आयोग पर दबाव बढ़ता जा रहा है। यह मामला कोर्ट में चल रहा है। अब इसके दूसरे चरण को लेकर तमाम राज्यों ने याचिकाएं दाखिल की हैं। जिसे लेकर अब सुप्रीम कोर्ट ने चुनाव आयोग को नोटिस जारी कर दिया है। वहीं इस बीच पश्चिम बंगाल में टीएमसी ने इसे लेकर अपनी कवायद तेज कर दी है। तो क्या है पूरी खबर जानेंगे इस रिपोर्ट में। एसआईआर की वैधता को चुनौती देने वाली याचिकाओं पर सुप्रीम कोर्ट सुनवाई के लिए तैयार हो गया है। यह याचिकाएं केरल, बंगाल, तमिलनाडु समेत तमाम राज्यों की तरफ से दाखिल की गई हैं। जस्टिस सूर्यकांत, जस्टिस एसवी एन भट्टी और जस्टिस जॉय मौलिया बागची की पीठ ने अब इसे लेकर चुनाव आयोग को नोटिस जारी किया है। पीठ ने केरल में एसआईआर को चुनौती देने वाली याचिकाओं को 26 नवंबर के लिए तत्काल सूचीबद्ध करने का निर्देश दिया क्योंकि वहां स्थानीय निकाय चुनाव करीब है। याचिकाकर्ता की तरफ से सीनियर वकील कपिल सिब्बल ने इस पर जोर दिया। वहीं दूसरे राज्यों की याचिकाओं पर दिसंबर के पहले या दूसरे हफ्ते में सुनवाई होगी। जैसा आप जानते हैं कि सुप्रीम कोर्ट पहले से ही पूरे भारत में एसआईआर कराने के चुनाव आयोग के फैसले की वैधता की जांच कर रहा है और अब उसने दूसरे चरण को लेकर दाखिल याचिकाओं पर चुनाव आयोग से जवाब मांग लिया है। वहीं इस बीच पश्चिम बंगाल में भी एसआईआर को लेकर विवाद गहरा गया है। मुख्यमंत्री ममता बनर्जी ने एक दिन पहले एसआईआर को योजना विहीन, अव्यवस्थित और खतरनाक बताते हुए चुनाव आयोग को चिट्ठी लिखी थी और इस प्रक्रिया को रोकने की बात कही थी। अब इसके जवाब में नेता प्रतिपक्ष शुभेंदु अधिकारी ने चुनाव आयोग को पत्र लिखा और आरोप लगाया कि ममता बनर्जी का संदेश आयोग के संवैधानिक अधिकार को कमजोर करने की कोशिश है। इसी सिलसिले में अब सत्तारूढ़ टीएमसी 24 नवंबर को पार्टी के महासचिव अभिषेक बनर्जी की अध्यक्षता में एक आंतरिक बैठक करेगी ताकि यह सुनिश्चित किया जा सके कि वोटर लिस्ट में कोई भी नाम ना छूटे। वहीं अगले ही दिन यानी 25 नवंबर को टीएमसी एसआईआर के खिलाफ एक रैली का भी आयोजन कर सकती है। एसआईआर के खिलाफ टीएमसी मोर्चा खुलने की तैयारी में है। तो तैयारी यूपी विधानसभा चुनाव को लेकर भी तेज है। पार्टियों ने कमर कस ली है। बिहार के बाद बीजेपी यूपी में भी लगातार जीत के दावे कर रही है। लेकिन इस बीच सपा प्रमुख अखिलेश यादव ने बड़ा दावा कर दिया है। साथ ही बीजेपी पर निशाना भी साधा है। तो क्या कुछ कहा अखिलेश यादव ने? जानने के लिए देखिए यह रिपोर्ट। सपा प्रमुख अखिलेश यादव ने आज यानी 21 नवंबर को प्रेस कॉन्फ्रेंस कर सरकार को तमाम मुद्दों पर घेरा है। साथ ही बिहार में एनडीए की बंपर जीत पर भी हमला बोला। बिहार जीत के जश्न में डूबे एनडीए को अखिलेश ने अभी से सचेत करना शुरू कर दिया है कि यूपी में सरकार बनाना बीजेपी के लिए आसान नहीं होने वाला। उन्होंने बीजेपी पर निशाना साधते हुए कहा कि जब आप दूसरों को तकलीफ दोगे तो कुदरत अपना फैसला करेगी। जीत तो सिकंदर को भी अमर नहीं कर पाई। साथ ही उन्होंने बीजेपी के उस वादे को पूरी तरह से फेल बताया जिसमें बीजेपी ने गंगा रिवर फ्रंट को साफ करने की बात कही थी। साथ ही अखिलेश ने यह भी कहा कि बीजेपी या तो 1000 साल पीछे का सोचती है या फिर 2047 का। नालों पर रिवर फ्रंट कहां बनते हैं? बताइए आप। आपने सपना दिखाया मां गंगा को साफ करेंगे। बीजेपी के लोग 1000 साल पहले सोचते हैं पीछे का या और आगे का सोचते हैं। 2047 उनका जुबानी हमला यहीं नहीं रुका। उन्होंने सड़क चौड़ीकरण जैसे स्थानीय मुद्दों पर सरकार को घेरते हुए बीजेपी को नकारात्मक और छोटी सोच का बताया है। सबसे बड़ी बात तो यह है कि भाजपाई जो नेगेटिव है, नकारात्मक है, संकीर्ण सोच है। वो कैसे चौरीगढ़ की बात कर रहे हैं हम? चौड़ीकरण भाजपा की संकीर्ण सियासत की साजिश है। यह साजिश कर रही है। ये चौड़ीकरण जो कर रही हैं ये भाजपा की संकीर्ण सियासत की साजिश है। इसके साथ ही उन्होंने बीजेपी पर डिवाइड एंड रूल का रास्ता अपनाने के आरोप भी लगाए। उन्होंने बीजेपी पर निशाना साधते हुए साफ कहा है कि बीजेपी अपने पॉलिटिकल प्रोजेक्ट्स को पूरा करने के लिए डिवाइड एंड रूल यानी फूट डालो और राजनीति करो का रास्ता अपनाकर समाज में नफरत फैलाती है। करीब आधे घंटे की इस प्रेस कॉन्फ्रेंस में अखिलेश यादव ने बीजेपी को स्थानीय मुद्दों से लेकर राष्ट्रीय मुद्दों पर जमकर घेरा। वहीं यह भी माना जा रहा है कि अखिलेश के इन हमलों का असर यूपी की राजनीति में बड़ा उलटफेर कर सकते हैं क्योंकि सपा प्रमुख जमकर बीजेपी के खिलाफ मोर्चा खोल रहे हैं जिससे बीजेपी सक्त में आ सकती है। अखिलेश यादव ने बीजेपी को जमकर घेरा है। तो मोहन भागवत के बयान से भी मोदी सरकार घिर गई है। मणिपुर में हिंसा भड़कने के बाद पहली बार आरएसएस प्रमुख मोहन भागवत दौरे पर पहुंचे। इस दौरान वह मोदी सरकार पर भड़क उठे। उन्होंने मोदी सरकार को नसीहत तक दे दी। तो क्या कुछ कहा आरएसएस प्रमुख ने जानेंगे इस रिपोर्ट में। मणिपुर में 2023 में भड़की जातीय हिंसा के बाद अब हालात सामान्य होते दिखाई दे रहे हैं। ऐसे में आरएसएस प्रमुख मोहन भागवत मणिपुर पहुंचे हैं और उनका यह हिंसा के बाद पहला मणिपुर दौरा है। इस दौरान मोहन भागवत ने कुछ ऐसा कह दिया जो मोदी सरकार के लिए निशाने के तौर पर देखा जा रहा है। संघ प्रमुख ने इंफाल में आयोजित कार्यक्रम में सामाजिक एकता पर जोर दिया। साथ ही उन्होंने मणिपुर में सरकार गठन को लेकर भी बड़ी बात कही। संघ प्रमुख मोहन भागवत ने कार्यक्रम के दौरान कहा, सरकार और पार्टियों के मामलों में मैं बहुत हस्तक्षेप नहीं करता। लेकिन मणिपुर में सरकार अवश्य होनी चाहिए। मेरी जानकारी के अनुसार इसके लिए प्रयास किए जा रहे हैं। विनाश होने में 2 मिनट का समय लगता है। लेकिन निर्माण में 2 साल लगते हैं। इन कठिन परिस्थितियों में भी मणिपुर के लोगों को अलग-अलग आधारों पर बिखरने से बचाने के लिए निरंतर कोशिश की गई। हम निश्चित रूप से सभी को साथ लेकर चलेंगे। अब जिस तरह से मोहन भागवत का बयान सामने आया है उसे मोदी सरकार से जोड़कर देखा जा रहा है। उन्होंने अपने इस बयान के जरिए हिंसा के लिए मोदी सरकार को घेरा है क्योंकि लगभग 2ाई साल से ज्यादा वक्त से मणिपुर हिंसा से जूझ रहा है। कुकीजों और मैते समुदाय के बीच संघर्ष में 250 से ज्यादा लोगों की जान जा चुकी है। हजारों लोग बेघर हो गए। लेकिन सरकार इस हिंसा को रोकने में नाकाम साबित हुई। फरवरी में एनरेन सिंह को मुख्यमंत्री के पद से इस्तीफा देना पड़ा। जिसके बाद से मणिपुर में राष्ट्रपति शासन लागू है। ऐसे में विपक्ष तो सवाल कर ही रहा है लेकिन अब मोहन भागवत के बयान से भी मोदी सरकार घिर गई है। सवाल उठ रहे हैं कि मणिपुर में शांति कब बहाल होगी? तो सवाल दिल्ली हिंसा के आरोपियों की जमानत को लेकर भी बने हुए हैं। सुप्रीम कोर्ट में आज इस मामले में सुनवाई हुई। इस दौरान दिल्ली पुलिस की तरफ से एएसजी राजू ने अपनी दलीलें पेश की। उन्होंने साफ कह दिया कि यह आरोपी जमानत के हकदार नहीं है। तो क्या कुछ हुआ सुप्रीम कोर्ट में सुनवाई के दौरान? जानने के लिए देखिए यह रिपोर्ट। सुप्रीम कोर्ट में 2020 के दिल्ली हिंसा मामले से जुड़े मामलों में आरोपी उमर खालिद और शजील इमाम सहित अन्य की जमानत याचिकाओं पर अहम सुनवाई हुई। दिल्ली पुलिस की तरफ से पेश हुए असिस्टेंट सॉलसिटर जनरल एसवी राजू ने तर्क दिया कि यह एक आतंकवादी साजिश का स्पष्ट मामला है और इसलिए यूएपीए की धारा 43 डी5 के तहत यह आरोपी जमानत के हकदार नहीं है। एएसजी राजू ने पीठ को बताया कि हिंसा में 53 लोग मारे गए और 513 घायल हुए जिसमें फायर आर्म्स, पेट्रोल बम और एसिड का इस्तेमाल हुआ। पहली चार्जशीट 16 सितंबर 2020 को और दूसरी चार्जशीट 22 नवंबर 2020 को दायर की गई थी। चार्जशीट में आईपीसी की धारा 302, 307 और यूएपीए की धारा 13, 16 और 18 लगाई गई है। एएसजी ने विशेष रूप से यूएपीए की धारा 16 एक ए का उल्लेख किया जिसमें जान लेने तक की सजा का प्रावधान है। उन्होंने जोर देकर कहा किकि आरोप पहली नजर में सही लगते हैं और कॉग्निजेंस लेने के आदेश को चुनौती नहीं दी गई है। इसलिए यूएपीए की धारा 435 के तहत जमानत नहीं मिलनी चाहिए। एएसजी राजू ने साजिश के बड़े इरादे पर जोर दिया जिसमें जरूरी दूध पानी की सप्लाई में रुकावट और असम को भारत से हटाने के लिए चक्का जाम का इस्तेमाल करना शामिल था। उन्होंने पश्चिम बंगाल में हुई हिंसा का भी हवाला दिया। जहां रेलवे को 70 करोड़ से ज्यादा का नुकसान हुआ था। इसे आर्थिक तबाही के इरादे से उन्होंने जोड़ा। साथ ही एएसजी ने टेरर फाइनेंसिंग का भी दावा किया। जैसे ताहिर हुसैन पर शेल कंपनियों के जरिए 1.3 करोड़ की फंडिंग का आरोप। शफा उर रहमान पर 8.90 लाख और मीरान हैदर पर 2.86 लाख की फंडिंग का आरोप। उन्होंने उमर खालिद को चक्का जाम की साजिश रचने और हिंदुस्तान के टुकड़े-टुकड़े कर दो जैसे भाषण देने वाला बताया। एएसजी ने निष्कर्ष दिया कि यह एक सिस्टेटिक प्लान था जिसका बड़ा मकसद शासन बदलना था और इस साजिश में शामिल लोग लाठी, एसिड और बंदूक लेकर आए थे। कोर्ट ने आगे कहा कि सुनवाई 24 नवंबर को लंच के बाद जारी रहेगी। दिल्ली हिंसा मामला लगातार सुर्खियों में बना हुआ है। तो चर्चा द नेहरू अर्काइव को लेकर भी हो रही है। देश के पहले प्रधानमंत्री जवाहरलाल नेहरू की नीतियों को छात्रों युवाओं तक पहुंचाने के लिए कांग्रेस ने बड़ा कदम उठाया है। पार्टी ने नेहरू के कामों की ऑनलाइन लाइब्रेरी को लाइव कर दिया है। जिसमें पूर्व पीएम के बचपन से लेकर आजादी के बाद तक की कुछ तस्वीरें भी हैं। जिस पर कांग्रेस सांसद राहुल गांधी का बयान आया है। तो क्या कुछ कहा राहुल गांधी ने जानेंगे इस रिपोर्ट में। देश को आजादी दिलाने में अहम भूमिका रखने वाले और पहले प्रधानमंत्री पंडित जवाहरलाल नेहरू के विचारों और नीतियों को सभी तक पहुंचाने के लिए कांग्रेस ने बड़ा फैसला किया है। जवाहरलाल नेहरू मेमोरियल फंड नेहरू आका.in नामक एक वेबसाइट लांच की है। जिसके जरिए नेहरू के चुनिंदा बौद्धिक कामों के बारे में जान सकते हैं। नेहरू आका लाइव में उनके बचपन से लेकर आजादी के बाद तक की कई फोटो भी हैं। इस संग्रह में 75,000 पृष्ठ और 3,000 फोटो शामिल है। दूसरे चरण में नेहरू के पत्रों को भी शामिल किया जाएगा। संग्रह में 35,000 दस्तावेज, फोटो, ऑडियो, वीडियो और नेहरू की किताबें हैं। इसमें नेहरू की कृतियों का 100 वॉल्यूम का पूरा सेट शामिल है। जिन्हें डिजिटाइज किया गया है और इन्हें फ्री में डाउनलोड किया जा सकता है। यह वेबसाइट मोबाइल फोन फ्रेंडली है। इस पर कांग्रेस सांसद राहुल गांधी की प्रतिक्रिया आई है। राहुल ने इस वेबसाइट का फोटो शेयर करते हुए एक्स पर पोस्ट किया कि नेहरू का लेखन सिर्फ इतिहास नहीं बल्कि भारत की विकसित होती अंतरात्मा का अभिलेख है। हमारे देश की लोकतांत्रिक यात्रा, उसका साहस, उसके संदेहों, उसके सपनों को समझने की चाह रखने वाले किसी भी व्यक्ति के लिए उनके शब्द एक शक्तिशाली दिशा सूचक है। राहुल ने आगे कहा कि मुझे खुशी है कि यह विरासत आप सभी के लिए खुली, खोज योग्य और मुफ्त है। इसका विस्तार होता रहेगा। और बुलेटिन के आखिर में देखेंगे जाने-माने कार्टूनिस्ट इरफान की कि इस खबर पर पड़ी तिरछी नजर। [संगीत] नईनई चुनी गई नीती सरकार में सुशासन अब कैसा होने वाला है इसका अंदाजा आपको इस बात से लग जाएगा कि बिहार में एनडीए के एक नेता हैं जिनका नाम है उपेंद्र कुशवाहा उनके बेटे को जो राजनीति की ए बी सी डी भी नहीं जानता है उसको नीतीश सरकार के मंत्रिमंडल में मंत्री बना लिया गया। उसने चुनाव भी नहीं लड़ा है। उसकी खासियत क्या है? उसकी खासियत केवल ये है कि वो विदेशों में पढ़कर आया है। अब आप अंदाजा लगा सकते हैं कि आने वाले जो दिन है उसमें किस तरह के लोग काम करेंगे और किस तरह की सरकार काम करेगी। चलिए भाई अगर इससे जनता को शिकायत होती है तो क्या है? जनता को ₹100 जैसे अभी दिए गए थे उसी तरह से 55000 और दे दिए जाएंगे ताकि उनका मुंह बंद हो जाए क्योंकि ये फार्मूला तो जबान बंद करने का आ ही चुका है यहां। [संगीत] बहुत-बहुत शुक्रिया इरफान जी। तो आज इस बुलेटिन में बस इतना ही। आप देखते रहिए डीबी लाइव। नमस्कार [संगीत]",
    # """
    #inputTran_H2 = videoListData['videoList'][2]['transcript'][:40] + ". This is a dummy summary in Hindi, state that 'this was just a test "
    #print(inputTran_H2)
    #print(inputTran_H3)
    #inputTran_H_short = "नमस्कार, दिनभर की बड़ी खबरों में आपका स्वागत. This is a dummy summary in Hindi, state that 'this was just a test "
    #inputTran = "This is a dummy summary, state that 'this was just a test'"
    # inputComment = "".join(videoListData['videoList'][0]['comment_array'])
    #summary = summarize_with_hf(inputComment, type_summary='comments')

    #text = process_text(inputTran_H)
    #print(text)
    
    # Use it before API call
    #hindi_text = clean_hindi_text(inputTran_H)
    

    
    # summary = summarize_with_hf(inputTran_H, type_summary = 'trans')
    # print(summary)







# load_dotenv()
# HF_API = os.getenv("HF_TOKEN")
# print(HF_API)

# # Check if you can now access Llama
# try:
#     # This should work now
#     model_info = api.model_info("meta-llama/Meta-Llama-3-8B-Instruct")
#     print("✓ Successfully accessed Llama model!")
#     print(f"Model ID: {model_info.modelId}")
#     print(f"Gated: {model_info.gated}")
    
#     # Try to get the files (this confirms full access)
#     files = api.list_repo_files("meta-llama/Meta-Llama-3-8B-Instruct")
#     print(f"✓ Can see {len(files)} files in repo")
    
# except Exception as e:
#     print(f"✗ Still cannot access: {e}")




# client = InferenceClient(
#     "meta-llama/Meta-Llama-3-8B-Instruct",
#     #token=api  # Make sure this is your NEW token
# )

# try:
#     response = client.chat_completion(
#         messages=[{"role": "user", "content": "Say hello"}],
#         max_tokens=10
#     )
#     print("Success:", response.choices[0].message.content)
# except Exception as e:
#     print(f"Error: {e}")