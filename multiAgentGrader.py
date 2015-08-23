#!/usr/bin/python2.4 
"""
The autograder for multi-agent pacman
"""

FINAL_GRADE = True
SEED = 'testing' # random seed at the beginnig of each question for more fairness in grading...
BIG_NEGATIVE = -10000

from game import Agent
from ghostAgents import RandomGhost, DirectionalGhost
import random, math, traceback, sys, os

def print_stack():
    apply(traceback.print_exception, sys.exc_info())

def fail(grades, message, question_id=None):
  grades['passed'] = False
  if question_id:
      grades[question_id][2] = message # this is the explanation for the grade...
  message = message.replace("\n","&&&\n&&&")
  print '&&& %s &&&' % message

def runWithAnnotations(name, lay, params, iterations = 1):
  """
  Runs a few games and outputs their statistics.
  """
  starttime = time.time()
  print '*** Running %s on' % name, lay,'%d time(s).' % iterations
  
  stats = pacman.main(params, iterations)
  
  print '*** Finished running %s on' % name, lay,'after %d seconds.' % (time.time() - starttime)
  print '*** Nodes generated while running:', stats['nodesExpanded']
  print '*** Number of total moves:', stats['numMoves']
  print '*** Score of final state:', stats['score']
  stats['time'] = time.time() - starttime
  return stats
    
    
class GradingAgent(Agent):
  def __init__(self, studentAgent, solutionAgents, alternativeDepthAgents = []):
    self.studentAgent = studentAgent
    self.solutionAgents = solutionAgents
    self.alternativeDepthAgents = alternativeDepthAgents
    self.suboptimalMoves = []
    self.offByOneMoves = []
    self.numGames = 0
    self.offByOne = False
    
  def registerInitialState(self, state):
    if 'registerInitialState' in dir(self.studentAgent):
      self.studentAgent.registerInitialState(state)
    for agent in self.solutionAgents + self.alternativeDepthAgents:
        if 'registerInitialState' in dir(agent):
            agent.registerInitialState(state)
    self.numGames += 1
    
  def getAction(self, state):
    if len(self.suboptimalMoves) > 0:
        # once the student has a made a suboptimal move, no need to look more into it!
        # then just finish the game with our agent...
        return self.solutionAgents[0].getAction(state)
    listOflists = [agent.getBestPacmanActions(state)[0] for agent in self.solutionAgents]
    optimalActions = set()
    for actions in listOflists:
        optimalActions.update(set(actions))
    studentAction = self.studentAgent.getAction(state)
    if studentAction not in optimalActions:
      alternativeLists = [agent.getBestPacmanActions(state)[0] for agent in self.alternativeDepthAgents]
      alternativeActions = set()
      for actions in alternativeLists:
        alternativeActions.update(set(actions))
      if studentAction in alternativeLists:
        self.offByOne = True
      else:
        self.suboptimalMoves.append( (state, studentAction, optimalActions ) )
    return listOflists[0][0]
  
  def checkFailure(self, grades, agentName, question_id = None):
    """
    Return +1 if have suboptimal moves.
    Return -1 if have only off by one depth moves.
    Return 0 otherwise.
    """
    nBad = len(self.suboptimalMoves)
    if nBad > 0:
      state, stuMove, opt = random.choice(self.suboptimalMoves)
#      msg = '%s performed %d suboptimal moves in a series of %d games.' % (agentName, nBad, self.numGames)
      msg = '%s performed a suboptimal move.' % agentName
      moves = 'Example: your agent chose %s instead of optimal moves %s in state:' % (str(stuMove), str(opt))
      fail(grades, '\n'.join([msg, moves, str(state)]), None) # None so that we don't include this multi-line explanation
      if question_id:
          grades[question_id][2] = msg
      return 1
    elif self.offByOne:
      return -1
    return 0
      
def q1(grades):
  """
  Tests for question 1
  
  Runs their reflex agent a few times and checks for victory!
  
  They get partial credit if they clear OpenClassic, but taking too much time...
  """
  points = 3
  grades[1]=[0,points,""]
  question_id = 1
  random.seed(SEED)
  
  lay = layout.getLayout('openClassic',3)
  pac = multiAgents.ReflexAgent()
  disp = textDisplay.PacmanGraphics()
  
  nGames = 3
  try:
    games = pacman.runGames(lay, pac, getRandomGhosts(1), disp, nGames)
  except:
    (type, value, trace) = sys.exc_info()
    fail(grades, 'Your ReflexAgent threw an exception: %s : %s' % (str(type), str(value)), question_id)
    print_stack()
    return
  
  wins = [game.state.isWin() for game in games].count(True)
  if wins != nGames: 
    fail(grades, 'Your ReflexAgent died on openClassic.',question_id)
    return
  
  averageScore = sum([game.state.getScore() for game in games ]) / nGames
  targetScores = [1200, 1125, 1050]
  grade = 0
#  for score in targetScores:
#    if averageScore >= score: grade += 1
  if averageScore >= 1200:
      grade = 3
      message = "" # full credit...
  elif averageScore >= 1000:
      grade = 2
      message = "Your reflex agent didn't complete openClassic quickly enough (your average score was %d and you needed at least 1200)" % averageScore
  else:
      grade = 1
      message = "Your reflex agent completed the maze without dying, but with trashing (it completed the maze too slowly: your average score was %d and you needed at least 1000 to have 2pts)." % averageScore
  grades[question_id] = [grade, points,message]
  
  # bonus question first estimate:
  # only if they did well in the first part...
  if grade < 1:
      grades['bonus1'] = BIG_NEGATIVE
      return
  random.seed(SEED)
  lay = layout.getLayout('trickyClassic',3)
  nGames = 3
  try:
    games = pacman.runGames(lay, pac, getDirectionalGhosts(4), disp, nGames)
  except Exception, inst:
    grades['bonus1'] = BIG_NEGATIVE
    print "EXCEPTION " + str(inst)
    print_stack()
    return
  averageScore = sum([game.state.getScore() for game in games ]) / nGames
  grades['bonus1'] = averageScore
  
  
def getRandomGhosts(n):
  return [RandomGhost(i + 1) for i in range(n)]
  
def getDirectionalGhosts(n):
  return [DirectionalGhost(i + 1) for i in range(n)]
  
def select(list, indices):
  """
  Return a sublist of elements given by indices in list.
  """
  return [list[i] for i in indices]

def construct_our_pacs(keyword_dict):
  pacs_without_stop = [multiAgentsSol.StaffMultiAgentSearchAgent(**keyword_dict) for i in range(3)]
  keyword_dict['keepStop'] = True
  pacs_with_stop = [multiAgentsSol.StaffMultiAgentSearchAgent(**keyword_dict) for i in range(3)]
  for pac in pacs_with_stop + pacs_without_stop:
    pac.verbose = False
  ourpac = [pacs_with_stop[0], pacs_without_stop[0]]
  alternative_pacs = select(pacs_with_stop + pacs_without_stop, [1,4,2,5])
  return (ourpac, alternative_pacs)

def comparison_checking(question_id):
    """
    Skeleton used for question 2, 3 and 4... 
    """
    if question_id == 2:
        points = 5
        theirpac = multiAgents.MinimaxAgent()
        keyword_dict = {}
        agent_name = "MinimaxAgent"
    elif question_id == 3:
        points = 3
        theirpac = multiAgents.AlphaBetaAgent()
        keyword_dict = {'alphabeta':True}
        agent_name = "AlphaBetaAgent"
    else: # question_id == 4:
        points = 3
        theirpac = multiAgents.ExpectimaxAgent()
        keyword_dict = {'expectimax':True}
        agent_name = "ExpectimaxAgent"
 
    grades[question_id]=[0, points, ""]
    random.seed(SEED)
    offByOne = False 
    
    ourpac, alternative_pacs = construct_our_pacs(keyword_dict)
    disp = textDisplay.PacmanGraphics()    

    lay = layout.getLayout('minimaxClassic')
    for depth in range(1, 4):
        theirpac.setDepth(depth)
        [p.setDepth(depth) for p in ourpac]
        if depth > 1:
            smaller_depth = depth-1
        else:
            smaller_depth = depth
            # depth = 0 doesn't work...
        [p.setDepth(smaller_depth) for p in alternative_pacs[:2]] # for off by one error...
        [p.setDepth(depth+1) for p in alternative_pacs[2:]]
        pac = GradingAgent(theirpac, ourpac, alternative_pacs)
        try:
            pacman.runGames(lay, pac, getRandomGhosts(2), disp, 1)
        except:
            (type, value, trace) = sys.exc_info()     
            fail(grades, 'Your %s threw an exception: %s : %s' % (agent_name, str(type), str(value)), question_id)
            print_stack()
            return     
        code = pac.checkFailure(grades, '%s(depth %d)' % (agent_name, depth), question_id)
        if code > 0: 
            return
        elif code < 0:
            offByOne = True
    
    if FINAL_GRADE:
        lay = layout.getLayout('smallClassic', 3)
        theirpac.setDepth(2)
        [p.setDepth(2) for p in ourpac]
        [p.setDepth(1) for p in alternative_pacs[:2]] # for off by one error...
        [p.setDepth(3) for p in alternative_pacs[2:]]
        pac = GradingAgent(theirpac, ourpac, alternative_pacs)
        try:
            pacman.runGames(lay, pac, getRandomGhosts(2), disp, 1)
        except:
            (type, value, trace) = sys.exc_info()     
            fail(grades, 'Your %s threw an exception: %s : %s' % (agent_name, str(type), str(value)), question_id)
            print_stack()
            return     
        code = pac.checkFailure(grades, agent_name, question_id)
        if code > 0:
            return
        elif code < 0:
            offByOne = True
  
    if offByOne:
        grades[question_id][0] = points -1
        grades[question_id][2] = "Your %s agent was off by one when using the depth variable: -1." % agent_name
    else:
        grades[question_id][0] = points
 

def q2(grades):
  """
  Tests for question 2
  
  Compares their agent to our minimax agent to ensure that all selected
  moves are optimal using score as an eval function. Try both the with and without 'stop' variations.
  """
  comparison_checking(2)
 
def q3(grades):
  """
  Tests for question 3
  
  Wraps their agent in our alphabeta agent to check that all selected
  moves are optimal and require less computation.
  """
  comparison_checking(3)
      
def q4(grades):
  """
  Tests for question 4
  
  Wraps their agent in our expectimax agent to check that all selected
  moves are optimal using score as an eval function.
  """
  comparison_checking(4)
   
def q5(grades):
  """
  Tests for question 5
  
  Runs their expectimax agent a few times and checks for victory!
  """
  points = 6
  grades[5]=[0,points,""]
  question_id = 5
  random.seed(SEED)
  nGames = 10
  
  pac = multiAgents.ExpectimaxAgent()
  pac.useBetterEvaluation()
  pac.setDepth(2)
  lay = layout.getLayout('mediumClassic')
  disp = textDisplay.PacmanGraphics()
  
  try:
    games = pacman.runGames(lay, pac, getRandomGhosts(2), disp, nGames)
  except:
    (type, value, trace) = sys.exc_info()
    fail(grades, 'Your better evaluation function with expectimax threw an exception: %s : %s' % (str(type), str(value)), question_id)
    print_stack()
    return  

  wins = [game.state.isWin() for game in games].count(True)
  if wins > 0:
      minWinScore = min([game.state.getScore() for game in games if game.state.isWin()])
  else:
      minWinScore = BIG_NEGATIVE
  if wins >=  nGames/2 and minWinScore > 200:
    grade = 6
    message = ""
  elif wins >= nGames /2:
    grade = 4
    message = "Your agent sometimes trashes: -2 (e.g. you won a game with a score of %d which means that you took way too long to finish the game)." % minWinScore
  elif wins == 0:
    grade = 0
    message = "You didn't win any game!"
  else:  # wins >= 1:
    if minWinScore > 200:
       grade = 3
       message = "You only won %d out of %d: -3." % (wins, nGames)
    else:
       grade = 1
       message = "You only won %d out of %d: -3; your agent sometimes trashes: -2 (e.g. you won a game with a score of %d which means that you took way too long to finish the game)." % (wins, nGames, minWinScore)

  grades[question_id] = [grade, points, message]
  
  # bonus 2 question first estimate:
  if grade < 6:
      grades['bonus2'] = BIG_NEGATIVE
      return
  random.seed(SEED)
  pac = multiAgents.AlphaBetaAgent()
  pac.useBetterEvaluation()
  pac.setDepth(2)
  lay = layout.getLayout('trickyClassic',3)
  nGames = 3
  try:
    games = pacman.runGames(lay, pac, getDirectionalGhosts(3), disp, nGames)
  except Exception, inst:
    grades['bonus2'] = BIG_NEGATIVE
    print "EXCEPTION " + str(inst)
    print_stack()
    return
  averageScore = sum([game.state.getScore() for game in games ]) / nGames
  grades['bonus2'] = averageScore   
  


def getKey(dict, key, default=0):
    """getKey(dict, key, default=0): Return default value if the key is not in the dictionary dict."""
    if key not in dict:
        return default
    else:
        return dict[key]

if __name__ == "__main__":
  if len(sys.argv) != 2: 
    print 'Usage: multiAgentGrader.py [transcript]\nUse - for stdout.'
    sys.exit(2)

  import pacman, time, layout, textDisplay
  textDisplay.SLEEP_TIME = 0
  textDisplay.DRAW_EVERY = 1000
  thismodule = sys.modules[__name__]
  
  # Our code
  import multiagentSolutions.multiAgents as multiAgentsSol
  
  # Their code
  import multiAgents
  
  if sys.argv[1] != '-':
      logfile = file(sys.argv[1], 'w')
      sys.stdout = logfile
      sys.stderr = logfile
  
  print 'Autograder transcript for project 2: Multi-agent Pacman', '%d-%d at %d:%d:%d' % time.localtime()[1:6]
  
  grades = {'passed': True}
  graded = range(1,6)

  for i in graded:
    print '\nQuestion %d:\n----------' % i
    # print >>sys.stderr, 'Grading question %d.' % i
    try:    
      getattr(thismodule, 'q%d' % i)(grades)
      grade = grades[i]
      grades['%d-text' % i] = 'Question %d: %d/%d - Explanation: %s' % (i, grade[0], grade[1], grade[2]) 
    except:
      (type, value, trace) = sys.exc_info()
      fail(grades, 'Question %d terminated with exception: %s : %s' % (i, str(type),str(value)))
      print_stack()
      grades['%d-text' % i] = 'Question %d gave an exception: %s : %s' % (i, str(type),str(value))  
  
  print '\nFinished at %d:%02d:%02d' % time.localtime()[3:6]
  if grades['passed']: print '@@@PASSED SANITY CHECKS@@@'
  print '+++ MINIMUM SCORE FOR THIS SUBMISSION +++'
  for i in graded:
    print grades['%d-text' % i]
  for bonus in ['bonus1', 'bonus2']:
      score = getKey(grades, bonus, 2*BIG_NEGATIVE)
      print '%s score: %d' % (bonus, score)
            
  print sum([grades[g][0] for g in graded])
  sys.stdout.close()
