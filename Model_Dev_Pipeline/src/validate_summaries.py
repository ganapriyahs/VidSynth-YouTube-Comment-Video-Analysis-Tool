import os
import sys
from dotenv import load_dotenv
import time
import json
import logging

# os.environ["DEEPEVAL_TELEMETRY_OPT_OUT"] = "YES"
# os.environ["DEEPEVAL_SHOW_INDICATOR"] = "NO"

from deepeval.metrics import SummarizationMetric
from deepeval.metrics import GEval
from deepeval.test_case import LLMTestCase, LLMTestCaseParams

# from deepeval import evaluate




def deepEval_summary_test(source, summary, metric, threshold = 0.3): # should probably increase threshold for passing
    """
    source: input or true reference data
    summary: generated summary of source
    threshold: minimium score to consider passing the test
    metric: object that defines what type of test is being conducted

    Returns:
    score: values between 0,1
    reason: string explanation from LLM judge
    passed: boolean true or false
    """

    test_case = LLMTestCase(
        input=source,
        actual_output=summary
    )

    metric.measure(test_case)
    passed = metric.score >= threshold

    return metric.score, metric.reason, passed



if __name__ == "__main__":
    """
    Information: 
    Tier	RPM	    RPD	    TPM	        Batch queue limit
    Free	3	    200	    40,000	    -
    Tier 1	500	    10,000	200,000	    2,000,000  -> I am on Tier 1

    """

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(message)s",
        handlers=[
            logging.FileHandler("log.txt", mode="w")
            # logging.StreamHandler()  # also prints to terminal
        ]
    )

    load_dotenv()

    api_key = os.getenv("OPENAI_API_KEY") # DeepEval internally grabs the key, no need to explicitly pass
    #print(api_key)

    DEFAULT_METRIC = SummarizationMetric(
        threshold=0.75,  # Score threshold for passing (0-1)
        model="gpt-4o-mini" #,  # can chose stronger model, but will be more expensive
        # assessment_questions=[  # Optional custom questions for evaluation
        #     "Does the summary capture the main points?",
        #     "Is the summary concise?",
        #     "Does the summary maintain factual accuracy?"
        # ]
    )

    transcript_metric = GEval(
        name="Transcript Summary Quality",
        criteria="""Evaluate whether the summary captures the key topics and information 
        from a YouTube transcript. The source transcript may be messy, lack punctuation, 
        and contain unclear speech. Focus on whether the summary conveys the essential 
        meaning rather than exact wording matches.""",
        evaluation_params=[LLMTestCaseParams.INPUT, LLMTestCaseParams.ACTUAL_OUTPUT],
        model= "gpt-4o-mini" #"gpt-4o"
    )

    comment_metric = GEval(
        name="Comment Summary Quality",
        criteria="""Evaluate whether the summary accurately represents a YouTube comment section.

        A good summary should:
        1. Correctly identify the overall sentiment (positive/negative/mixed)
        2. Capture the dominant themes that multiple commenters mention
        3. Not present single-comment opinions as major themes
        4. Note any requests or suggestions if they appear repeatedly
        
        A good summary does NOT need to:
        - Mention every single comment
        - Preserve exact wording from comments
        - Capture one-off jokes or tangential remarks
        
        Score generously if the summary gets the sentiment and main themes right,
        even if it misses minor details or includes slight overrepresentations.""",
        evaluation_params=[LLMTestCaseParams.INPUT, LLMTestCaseParams.ACTUAL_OUTPUT],
        model= "gpt-4o-mini" #"gpt-4o"
    )

    try:
        with open('videoList.json', 'r', encoding='utf-8') as f:
            videoListData = json.load(f)
    except FileNotFoundError:
        print("Error: Run 'initialize_validation_set..py first'")
        sys.exit(1)

    passCount = 0

    for test in videoListData['videoList']:
        #print(f"Attempting to Judge summaries for {test['video_url']}")
        logging.info(f"Attempting to Judge summaries for {test['video_url']}")

        # if test.get('comment_eval_score') is not None and test.get('trans_eval_score') is not None:
        #     print("Already Validated: skipping this test...")
        #     continue

        # get existing data
        tempTrans = test['transcript']
        tempComments = "".join(test['comment_array'])

        tempSummaryTrans = test["trans_summary"]
        tempSummaryComments = test["comment_summary"]

        # test for transcript
        score, reason, passed = deepEval_summary_test(
            source = tempTrans, 
            summary = tempSummaryTrans, 
            metric=transcript_metric,
            threshold = 0.75
        )
        if passed: passCount +=1

        test["trans_eval_score"] = score
        test["trans_eval_reason"] = reason
        #print(f"Transcript Test passed? {passed}, Score was: {score}, Reason saved to .json file")
        logging.info(f"Transcript Test passed? {passed}, Score was: {score}, Reason also saved to .json file.")
        logging.info(f"Reason for transcript score: {reason}")
        

        # test for comments
        score, reason, passed = deepEval_summary_test(
            source = tempComments, 
            summary = tempSummaryComments, 
            metric=comment_metric,
            threshold = 0.75
        )
        if passed: passCount +=1

        test["comment_eval_score"] = score
        test["comment_eval_reason"] = reason
        #print(f"Comments Test passed? {passed}, Score was: {score}, Reason saved to .json file\n")
        logging.info(f"Comments Test passed? {passed}, Score was: {score}, Reason also saved to .json file.")
        logging.info(f"Reason for comment score: {reason}")

        with open('videoList.json', 'w', encoding='utf-8') as f:
            json.dump(videoListData, f, indent=2, ensure_ascii=False)

        # avoid API limit for tier 1 
        logging.info("Sleeping for 5 to avoid api limit\n")
        time.sleep(5)
    
    print(f"{passCount}/20 tests passed")
    logging.info(f"{passCount}/20 tests passed")
    if passCount >= 15:
        print("Minimum vallidation criteria has been met: push Llama3.1-8B-Instruct to registry")
        logging.info("Minimum vallidation criteria has been met: push Llama3.1-8B-Instruct to registry")
        # trigger script to push model 
        

