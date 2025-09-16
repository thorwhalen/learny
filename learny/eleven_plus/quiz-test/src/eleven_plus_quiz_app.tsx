import React, { useState, useEffect } from 'react';
import gameParamsData from './11plus_words_game_params.json';

const ElevenPlusQuizApp = () => {
  // Game configuration loaded from JSON
  const [gameParams, setGameParams] = useState(gameParamsData);
  const [words, setWords] = useState(Object.keys(gameParamsData));

  // Initialize data on component mount
  useEffect(() => {
    setGameParams(gameParamsData);
    setWords(Object.keys(gameParamsData));
  }, []);

  // App state
  const [gameMode, setGameMode] = useState('menu');
  const [currentQuestion, setCurrentQuestion] = useState(null);
  const [score, setScore] = useState({ correct: 0, total: 0 });
  const [feedback, setFeedback] = useState(null);
  const [usedWords, setUsedWords] = useState(new Set());


  const shuffleArray = (array) => {
    const shuffled = [...array];
    for (let i = shuffled.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
    }
    return shuffled;
  };

  const generateSynonymQuestion = () => {
    const availableWords = words.filter(word => !usedWords.has(word));
    if (availableWords.length === 0) {
      setUsedWords(new Set());
      return generateSynonymQuestion();
    }

    const word = availableWords[Math.floor(Math.random() * availableWords.length)];
    const wordConfig = gameParams[word];
    
    if (!wordConfig) {
      return generateSynonymQuestion(); // Skip this word if no config found
    }
    
    // Randomly choose between synonym or antonym question
    const isAntonym = Math.random() < 0.5;
    const questionType = isAntonym ? 'antonyms' : 'synonyms';
    const questionConfig = wordConfig[questionType];
    
    if (!questionConfig) {
      return generateSynonymQuestion(); // Skip if no config for this question type
    }

    const options = [...questionConfig.choices];
    const correctAnswer = questionConfig.correct;

    return {
      type: 'synonym',
      word,
      question: `What is a ${isAntonym ? 'antonym' : 'synonym'} for "${word}"?`,
      options: shuffleArray(options),
      correctAnswer,
      explanation: `"${correctAnswer}" is a ${isAntonym ? 'antonym' : 'synonym'} of "${word}".`
    };
  };

  const generateOddOneOutQuestion = () => {
    const availableWords = words.filter(word => !usedWords.has(word));
    if (availableWords.length === 0) {
      setUsedWords(new Set());
      return generateOddOneOutQuestion();
    }

    const word = availableWords[Math.floor(Math.random() * availableWords.length)];
    const wordConfig = gameParams[word];
    
    if (!wordConfig?.odd_one_out) {
      return generateOddOneOutQuestion(); // Skip this word if no config found
    }
    
    const questionConfig = wordConfig.odd_one_out;
    const options = [...questionConfig.choices];
    const correctAnswer = questionConfig.correct;

    return {
      type: 'odd_one_out',
      word,
      question: 'Which word does NOT belong with the others?',
      options: shuffleArray(options),
      correctAnswer,
      explanation: `"${correctAnswer}" has the opposite meaning to the other words.`
    };
  };

  const generateAnalogyQuestion = () => {
    const availableWords = words.filter(word => !usedWords.has(word));
    if (availableWords.length === 0) {
      setUsedWords(new Set());
      return generateAnalogyQuestion();
    }

    const word = availableWords[Math.floor(Math.random() * availableWords.length)];
    const wordConfig = gameParams[word];
    
    if (!wordConfig?.analogies) {
      return generateAnalogyQuestion(); // Skip this word if no config found
    }
    
    const questionConfig = wordConfig.analogies;
    const options = [...questionConfig.choices];
    const correctAnswer = questionConfig.correct;
    
    // Extract analogy components from the JSON config
    const first = questionConfig.first;
    const second = questionConfig.second;
    const relation = questionConfig.relation;

    return {
      type: 'analogy',
      word: word,
      question: `${first} is to ${second} as ${word} is to ___`,
      options: shuffleArray(options),
      correctAnswer,
      explanation: `${first} and ${second} are ${relation}s, just as ${word} and ${correctAnswer} are ${relation}s.`
    };
  };

  const generateQuestion = (mode) => {
    switch (mode) {
      case 'synonyms':
        return generateSynonymQuestion();
      case 'odd_one_out':
        return generateOddOneOutQuestion();
      case 'analogies':
        return generateAnalogyQuestion();
      default:
        return generateSynonymQuestion();
    }
  };

  const startGame = (mode) => {
    setGameMode(mode);
    setScore({ correct: 0, total: 0 });
    setUsedWords(new Set());
    setFeedback(null);
    
    const firstQuestion = generateQuestion(mode);
    setCurrentQuestion(firstQuestion);
  };

  const handleAnswer = (selectedAnswer) => {
    const isCorrect = selectedAnswer === currentQuestion.correctAnswer;
    const newScore = {
      correct: score.correct + (isCorrect ? 1 : 0),
      total: score.total + 1
    };
    
    setScore(newScore);
    setUsedWords(prev => new Set([...prev, currentQuestion.word]));
    
    setFeedback({
      isCorrect,
      explanation: currentQuestion.explanation,
      selectedAnswer,
      correctAnswer: currentQuestion.correctAnswer
    });
  };

  const nextQuestion = () => {
    setFeedback(null);
    const newQuestion = generateQuestion(gameMode);
    setCurrentQuestion(newQuestion);
  };

  const backToMenu = () => {
    setGameMode('menu');
    setCurrentQuestion(null);
    setFeedback(null);
    setScore({ correct: 0, total: 0 });
    setUsedWords(new Set());
  };

  const percentage = score.total > 0 ? Math.round((score.correct / score.total) * 100) : 0;

  if (gameMode === 'menu') {
    return (
      <div className="min-h-screen p-4 bg-gradient-to-br from-purple-400 via-pink-500 to-blue-500">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-12 floating">
            <h1 className="text-6xl font-bold text-white mb-4 drop-shadow-lg">
              🎓 11+ Vocabulary Quiz
            </h1>
            <p className="text-2xl text-white/90 font-medium mb-2">
              Master your vocabulary with interactive quizzes
            </p>
            <div className="score-badge inline-block text-lg">
              📚 {words.length} essential words • 3 question types
            </div>
          </div>
          
          <div className="grid md:grid-cols-3 gap-8">
            <div 
              onClick={() => startGame('synonyms')}
              className="game-card game-mode-card p-8 cursor-pointer bg-gradient-to-r from-purple-500 to-purple-600 text-white rounded-2xl hover:shadow-xl transition-all duration-300 group"
            >
              <div className="text-center">
                <div className="text-5xl mb-4 group-hover:scale-110 transition-transform">📚</div>
                <h3 className="text-2xl font-bold mb-3">Synonyms & Antonyms</h3>
                <p className="text-white/90 mb-4 text-lg">Find words with similar or opposite meanings</p>
                <div className="bg-white/20 backdrop-blur-sm rounded-lg p-4">
                  <p className="text-sm text-white/90">
                    <strong>Example:</strong> What is a synonym for "abundant"?
                  </p>
                </div>
              </div>
            </div>

            <div 
              onClick={() => startGame('odd_one_out')}
              className="game-card game-mode-card p-8 cursor-pointer bg-gradient-to-r from-green-500 to-green-600 text-white rounded-2xl hover:shadow-xl transition-all duration-300 group"
            >
              <div className="text-center">
                <div className="text-5xl mb-4 group-hover:scale-110 transition-transform">🔍</div>
                <h3 className="text-2xl font-bold mb-3">Odd One Out</h3>
                <p className="text-white/90 mb-4 text-lg">Identify which word doesn't belong</p>
                <div className="bg-white/20 backdrop-blur-sm rounded-lg p-4">
                  <p className="text-sm text-white/90">
                    <strong>Example:</strong> Which doesn't belong: happy, joyful, sad, cheerful?
                  </p>
                </div>
              </div>
            </div>

            <div 
              onClick={() => startGame('analogies')}
              className="game-card game-mode-card p-8 cursor-pointer bg-gradient-to-r from-blue-500 to-blue-600 text-white rounded-2xl hover:shadow-xl transition-all duration-300 group"
            >
              <div className="text-center">
                <div className="text-5xl mb-4 group-hover:scale-110 transition-transform">🔗</div>
                <h3 className="text-2xl font-bold mb-3">Analogies</h3>
                <p className="text-white/90 mb-4 text-lg">Complete word relationships and patterns</p>
                <div className="bg-white/20 backdrop-blur-sm rounded-lg p-4">
                  <p className="text-sm text-white/90">
                    <strong>Example:</strong> Hot is to cold as light is to ___
                  </p>
                </div>
              </div>
            </div>
          </div>

          <div className="mt-12 text-center">
            <div className="main-card p-6 max-w-2xl mx-auto">
              <h3 className="text-xl font-bold text-gray-800 mb-3">About This Quiz</h3>
              <p className="text-gray-600">
                Practice with {words.length} carefully selected vocabulary words from the 11+ curriculum. 
                Each question type develops different language skills essential for exam success.
              </p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (!currentQuestion) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center">
        <div className="text-center">
          <div className="text-4xl mb-4">🔄</div>
          <p className="text-xl text-indigo-700">Loading question...</p>
        </div>
      </div>
    );
  }

  const modeConfig = {
    synonyms: { icon: '📚', title: 'Synonyms & Antonyms', color: 'indigo' },
    odd_one_out: { icon: '🔍', title: 'Odd One Out', color: 'green' },
    analogies: { icon: '🧩', title: 'Analogies', color: 'purple' }
  };

  const config = modeConfig[gameMode];

  return (
    <div className="min-h-screen p-4 bg-gradient-to-br from-purple-400 via-pink-500 to-blue-500">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="main-card question-card p-6 mb-8">
          <div className="flex justify-between items-center">
            <div className="flex items-center space-x-3">
              <span className="text-4xl">{config.icon}</span>
              <h1 className="text-3xl font-bold bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent">
                {config.title}
              </h1>
            </div>
            <button
              onClick={backToMenu}
              className="px-6 py-3 bg-gray-500 text-white rounded-xl hover:bg-gray-600 transition-all duration-300 font-semibold hover:transform hover:-translate-y-1"
            >
              🏠 Back to Menu
            </button>
          </div>
        </div>

        {/* Score Display */}
        <div className="main-card p-6 mb-8">
          <div className="flex justify-between items-center">
            <div className="flex space-x-8">
              <div className="text-center">
                <div className="text-3xl font-bold text-green-600">{score.correct}</div>
                <div className="text-sm text-gray-600 font-medium">Correct</div>
              </div>
              <div className="text-center">
                <div className="text-3xl font-bold text-blue-600">{score.total}</div>
                <div className="text-sm text-gray-600 font-medium">Total</div>
              </div>
              <div className="text-center">
                <div className="text-3xl font-bold text-purple-600">{percentage}%</div>
                <div className="text-sm text-gray-600 font-medium">Accuracy</div>
              </div>
            </div>
            <div className="text-right">
              <div className="score-badge">
                📚 {usedWords.size} / {words.length} words
              </div>
            </div>
          </div>
        </div>

        {/* Question Card */}
        <div className="main-card question-card p-8 mb-8">
          <div className="text-center mb-8">
            <h2 className="text-3xl font-bold mb-6 bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent">
              {currentQuestion.question}
            </h2>
            {currentQuestion.word && (
              <div className="text-xl text-gray-600 mb-6">
                Focus word: <span className="font-bold text-purple-700">{currentQuestion.word}</span>
              </div>
            )}
          </div>

          {/* Options */}
          <div className="grid grid-cols-1 gap-4 mb-8">
            {currentQuestion.options.map((option, index) => (
              <button
                key={index}
                onClick={() => handleAnswer(option)}
                disabled={feedback !== null}
                className={`answer-btn p-6 text-left border-2 rounded-xl transition-all duration-300 font-medium text-lg ${
                  feedback === null
                    ? 'bg-white border-gray-300 hover:bg-purple-50 hover:border-purple-400 hover:text-purple-700'
                    : feedback.selectedAnswer === option
                    ? feedback.isCorrect
                      ? 'correct-answer'
                      : 'wrong-answer'
                    : option === currentQuestion.correctAnswer
                    ? 'correct-answer'
                    : 'bg-gray-100 border-gray-300 text-gray-500'
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="flex-1">{option}</span>
                  {feedback !== null && option === currentQuestion.correctAnswer && (
                    <span className="text-green-600 text-2xl ml-3">✓</span>
                  )}
                  {feedback !== null && feedback.selectedAnswer === option && !feedback.isCorrect && (
                    <span className="text-red-600 text-2xl ml-3">✗</span>
                  )}
                </div>
              </button>
            ))}
          </div>

          {/* Feedback */}
          {feedback && (
            <div className={`rounded-xl p-6 mb-8 ${
              feedback.isCorrect ? 'feedback-success' : 'feedback-error'
            }`}>
              <div className="flex items-center space-x-3 mb-3">
                <span className="text-3xl">
                  {feedback.isCorrect ? '🎉' : '�'}
                </span>
                <h3 className={`text-2xl font-bold ${
                  feedback.isCorrect ? 'text-green-800' : 'text-red-800'
                }`}>
                  {feedback.isCorrect ? 'Excellent!' : 'Not quite right!'}
                </h3>
              </div>
              <p className={`text-lg mb-4 ${
                feedback.isCorrect ? 'text-green-700' : 'text-red-700'
              }`}>
                {feedback.explanation}
              </p>
              {!feedback.isCorrect && (
                <p className="text-gray-700">
                  You selected: <span className="font-semibold text-red-600">{feedback.selectedAnswer}</span><br/>
                  Correct answer: <span className="font-semibold text-green-600">{feedback.correctAnswer}</span>
                </p>
              )}
            </div>
          )}

          {/* Next Question Button */}
          {feedback && (
            <div className="text-center">
              <button
                onClick={nextQuestion}
                className="btn-primary text-xl px-8 py-4"
              >
                ➡️ Next Question
              </button>
            </div>
          )}
        </div>

        {/* Progress Indicator */}
        <div className="main-card p-6">
          <div className="flex justify-between items-center mb-3">
            <span className="text-lg font-bold text-gray-700">Progress</span>
            <span className="text-sm text-gray-600">
              {usedWords.size} of {words.length} words practiced
            </span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-4 overflow-hidden">
            <div 
              className="progress-bar bg-gradient-to-r from-purple-500 to-pink-500 h-4 rounded-full"
              style={{ width: `${(usedWords.size / words.length) * 100}%` }}
            ></div>
          </div>
          <div className="mt-3 text-center">
            <span className="text-sm text-gray-600 font-medium">
              {((usedWords.size / words.length) * 100).toFixed(1)}% of vocabulary covered
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ElevenPlusQuizApp;