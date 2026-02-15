from simple_state_machine import StateMachine

#NOTE: this file is not used for anything besides storing the state machines in human readable format. 
# actual state machines are saved in pickle files. 

problem_state_machine = StateMachine("problem", 
                                               ["OK", "Problem"],
                                               ["problem_detected", "problem_cleared"],
                                               "OK",
                                               {"OK":{"problem_detected":"Problem",
                                                      "problem_cleared":"OK"},
                                                "Problem":{"problem_detected":"Problem",
                                                           "problem_cleared":"OK"}})

busy_state_machine = StateMachine("busy",["Free","Busy"],
                                                   ["move","finished"],
                                                   "Free",
                                                   {"Free":{"move":"Busy",
                                                            "finished":"Free"},
                                                    "Busy":{"move":"Busy",
                                                            "finished":"Free"}
                                                          })

dialogue_state_machine = StateMachine("dialogue", ["Silent","SpokeToMe", "BusyCheck", 
                                                             "LookAtUser", "AnnounceBusy", "StartDialogue2", 
                                                             "AnswerHuman", "WaitHumanQuestion1", "CheckProblemAndBusy",
                                                               "StartDialogue1", "Goodbye", "AskIfHumanIsAvailable",
                                                               "AnnounceProblem", "WaitHumanQuestion2", "ClearProblem"],
                                                            ["alone", "dialogue_end", "saw_human", "heard_human",
                                                             "yes","no", "no_problem", "busy", "idle", "problem_detected",
                                                             "dialogue_init", "human_question", "robot_finished", "timeout"],
                                                            "Silent",
                                                            {"Silent":{"alone":"Silent",
                                                                       "saw_human":"CheckProblemAndBusy",
                                                                       "heard_human":"SpokeToMe",
                                                                       },
                                                             "SpokeToMe":{"no":"Silent",
                                                                          "yes":"BusyCheck",
                                                                          },
                                                             "BusyCheck":{"idle":"LookAtUser",
                                                                          "busy":"AnnounceBusy",}, 
                                                             "LookAtUser":{"saw_human":"StartDialogue2",},
                                                             "AnnounceBusy":{"robot_finished":"Goodbye",},
                                                             "StartDialogue2":{"dialogue_init":"AnswerHuman",}, 
                                                             "AnswerHuman":{"robot_finished":"WaitHumanQuestion2",},
                                                             "WaitHumanQuestion1":{"human_question":"AnswerHuman",
                                                                                   "timeout":"ClearProblem",},
                                                             "CheckProblemAndBusy":{"busy":"Silent",
                                                                                    "no_problem":"Silent",
                                                                                    "problem_detected":"StartDialogue1"},
                                                             "StartDialogue1":{"dialogue_init":"AskIfHumanIsAvailable",},
                                                             "Goodbye":{"dialogue_end":"Silent",},
                                                             "AskIfHumanIsAvailable":{"yes":"AnnounceProblem",
                                                                                      "robot_finished":"Goodbye",},
                                                             "AnnounceProblem":{"robot_finished":"WaitHumanQuestion1",},
                                                             "WaitHumanQuestion2":{"human_question":"AnswerHuman",
                                                                                   "timeout":"Goodbye",},
                                                             "ClearProblem":{"robot_finished":"Goodbye",}})