import requests
import functools
import pandas as pd # Package to manipulate tables of data
import seaborn as sns # Package to create visual heatmap
import matplotlib.pyplot as plt # Package to plot heatmap

api_key = "<API - KEY>" # Temporary Api token provided to CourseAdmin user
headers = {"Authorization": api_key} # Set authorization token in header that will be passed with each api request
url = 'http://api.codepost.io/' # url
s = requests.Session()

#######  Calculate the average grade of an assignment
def get_submissions(assignmentID):
    r = requests.get(url + 'assignments/%s/submissions/' % str(assignmentID), headers=headers)
    return r.json()

def avg_grade(assignmentID):
    submissions = get_submissions(assignmentID=assignmentID) # Get all submissions for an assignment
    graded_submissions = [sub for sub in submissions if sub['grade']] # Filter out ungraded submissions (grade == null)
    avg_grade = functools.reduce(lambda x,y: x + y['grade'], graded_submissions, 0) / len(graded_submissions)
    print("Average grade on this assignment is %s" % avg_grade)

avg_grade(2) # Get the average grade for assignment with id 2


#######  Example 2: For a given assignment, create and plot a heatmap of rubricComment usage by Grader
def getCommentAuthor(commentID):
    r = requests.get(url + 'comments/%s/' % str(commentID), headers=headers)
    return r.json()['author']

def heatmap(assignmentID):
    # hmap is a dictionary mapping {'graderEmail':{ ('rubricCommentName', 'rubricCommentID') : numTimesUsed }}
    hmap = {}

    # Get array of rubricComments for an assignment, each of which has fields 'id', 'text', and 'comments' (array of comment ids)
    r = requests.get(url + 'assignments/%s/rubric/' % str(assignmentID), headers=headers)
    for rubricComment in r.json()['rubricComments']:
        rubricCommentIdentifier = (rubricComment['text'], rubricComment['id']) # Create a unique identifier of (text, id)
        linkedCommentIDs = rubricComment['comments'] # Get all the submission comments that are linked to the rubricComment
        for commentID in linkedCommentIDs:
            # For each submission comment linked to the rubric comment, get the comment's author
            grader =requests.get(url + 'comments/%s/' % str(commentID), headers=headers).json()["author"]
            # Update the mapping
            if grader in hmap and rubricCommentIdentifier in hmap[grader]:
                hmap[grader][rubricCommentIdentifier] += 1
            elif grader in hmap:
                hmap[grader][rubricCommentIdentifier] = 1
            else:
                hmap[grader] = {rubricCommentIdentifier: 1}

    # Heatmap styling and plotting - once the data is pulled, package choice and styling up to you :)
    dataframe = pd.DataFrame(hmap)
    dataframe.fillna(0, inplace=True) # Fill in zeroes for empty grader, rubricComment pairs
    dataframe.rename(columns=lambda x: x.split("@")[0],inplace=True) # strip out netID for plot simplicity
    dataframe = dataframe.reindex(sorted(dataframe.columns), axis=1) # sort columns
    sns.heatmap(dataframe, cmap=sns.light_palette("green"), cbar_kws={'label': '# Comments'})
    plt.xlabel('Grader emails')
    plt.ylabel('Rubric Comment text - id')
    plt.tight_layout()
    plt.show()

heatmap(2) # Plot a heatmap for assignment with id 2