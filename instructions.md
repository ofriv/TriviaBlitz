Exercise 2 - Real-time multiplayer trivia competition
(Reminder: Remember the ‘wow’ factor)
In this exercise I will again give you initial guidance and guidelines but you can implement it
as you wish. This will be your first “baby”
You need to implement a real-time multiplayer trivia competition.
First you should use a “smart” LLM (like gpt 5.5) to generate for you a ‘database’ of general
trivia questions and answers. Create at least 250 questions(and a difficulty rating between
1-10 to each question) and answers and 3 more ‘wrong’ answers for each question using
that LLM. Then have a smart LLM go over those questions and make sure all questions are
unique (no repetitions). Then have less smart LLMs (for example gemma in multiple sizes or
any LLMs that you choose) try to solve each of these questions. If the ‘less smart’ LLMs
were not able to answer correctly, remove that question from the ‘database’ as it might be
too hard.
Run the above using any tools that you want once(of course do it with code and not
manually).
Remember that when you ask an LLM for ‘many’ things in a single prompt the quality of the
answer might become weak so you might need to batch it to multiple requests.
(Sometimes when LLMs create multiple possible answers to questions they make the correct
answer longer than the others so make sure to fix it if that’s the case).
So the output of everything above should be a csv of at least 250 questions with a correct
answer to each one and 3 extra ‘wrong answers’ and a difficulty column.
Then you should take this data and convert it into a simple sqlite database.
(Remember- commit and push to your private github)
You should implement the multiplayer server(backend) using python and socket.io.
However, you can implement the frontend with any technology that you wish (for examplenext.js, react etc) and using any tool.
The competition should work like this:
The clients connect to the server and the server waits for 30 seconds for the matchmaking of
the user against other users. After the time ends, the game begins with all the users that
waited. A random trivia question is shown for a couple of seconds (you decide) on all of the
players’ screens and 4 options are displayed. The user should choose the correct answer.
The users that answer faster should get more points. If the user answered incorrectly, he
should get 0 points. Each game will include 10 questions and after those questions there will
be shown a leaderboard with all the scores and winner. If just a single human player is in the
game, you should add between 1-3 bot users to the game so he won’t play against himself.
Of course make sure that the bots don’t answer too quickly and that they sometimes have
mistakes.
In each game, each player will get 3 different ‘helps’ (one of each) : one is 50/50 that
removes 2 of the incorrect answers. The second is ‘call a friend’ (you should use any LLM
via api (use PydanticAI for the call) and ask him to give advice for the player, make it fun).
The third is ‘Double the score’ which will double the score of that question (players should
use it strategically when they are certain they know the answer).
During the game, the players will be able to send messages to each other(basic chat) and/or
send emojis.
In order to make the game more interesting, make the difficulty adaptive to the human
players. If the human players answer a question correctly then the next question should be
harder (and if incorrectly, the next question should be easier).
You should have a sqlite database that will save some data(you decide which data and for
which purposes).
When everything runs fine, you can use https://pinggy.io/ (or ngrok) to get a url for your
friends to connect to your pc and play with you the game. You can also of course upload
everything to a cloud provider like Render/azure etc (completely optional but highly
recommended). Play with some friends/family and listen to what they have to say about the
competition.
You can add any other things that you wish to the project including any kind of feature,
animations, graphics, mobile phone support or really anything that you feel will make it great.
Add at least 2 extra features/changes to what I wrote.
As this exercise is ‘your own’ make sure to invest some time in making it your own
(your own style, changes from feedback that you got from others etc).