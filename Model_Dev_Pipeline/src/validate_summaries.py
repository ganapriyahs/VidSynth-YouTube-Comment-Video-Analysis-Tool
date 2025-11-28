import os
import sys
from dotenv import load_dotenv
import time
import json

os.environ["DEEPEVAL_TELEMETRY_OPT_OUT"] = "YES" # this currently does not work to suppress terminal outputs
os.environ["DEEPEVAL_SHOW_INDICATOR"] = "NO"

from deepeval.metrics import SummarizationMetric
from deepeval.test_case import LLMTestCase

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

    load_dotenv()

    api_key = os.getenv("OPENAI_API_KEY") # DeepEval internally grabs the key, no need to explicitly pass
    #print(api_key)

    DEFAULT_METRIC = SummarizationMetric(
        threshold=0.3,  # Score threshold for passing (0-1)
        model="gpt-4o-mini" #,  # can chose stronger model, but will be more expensive
        # assessment_questions=[  # Optional custom questions for evaluation
        #     "Does the summary capture the main points?",
        #     "Is the summary concise?",
        #     "Does the summary maintain factual accuracy?"
        # ]
    )

    try:
        with open('videoList.json', 'r', encoding='utf-8') as f:
            videoListData = json.load(f)
    except FileNotFoundError:
        print("Error: Run 'initialize_validation_set..py first'")
        sys.exit(1)

    passCount = 0

    for test in videoListData['videoList']:
        print(f"Attempting to Judge summaries for {test['video_url']}")

        # NOTE: uncommet if you have a partial run and don't want to rerun all tests
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
            metric=DEFAULT_METRIC
        )
        if passed: passCount +=1

        test["trans_eval_score"] = score
        test["trans_eval_reason"] = reason
        print(f"Transcript Test passed? {passed}, Score was: {score}, Reason saved to .json file")
        

        # test for comments
        score, reason, passed = deepEval_summary_test(
            source = tempComments, 
            summary = tempSummaryComments, 
            metric=DEFAULT_METRIC
        )
        if passed: passCount +=1

        test["comment_eval_score"] = score
        test["comment_eval_reason"] = reason
        print(f"Comments Test passed? {passed}, Score was: {score}, Reason saved to .json file\n")

        with open('videoList.json', 'w', encoding='utf-8') as f:
            json.dump(videoListData, f, indent=2, ensure_ascii=False)

        # avoid API limit for tier 1 
        time.sleep(5)

    print(f"{passCount}/20 tests passed")
    if passCount >= 15:
        print("Minimum vallidation criteria has been met: initiating model push to registry")
        # trigger script to push model 
        

