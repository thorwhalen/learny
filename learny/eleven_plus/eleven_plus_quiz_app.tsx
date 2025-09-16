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
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-6">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-12">
            <h1 className="text-5xl font-bold text-indigo-900 mb-4">11+ Vocabulary Quiz</h1>
            <p className="text-xl text-indigo-700">Master your vocabulary with interactive quizzes</p>
            <p className="text-lg text-indigo-600 mt-2">{words.length} essential words • 3 question types</p>
          </div>
          
          <div className="grid md:grid-cols-3 gap-8">
            <div 
              onClick={() => startGame('synonyms')}
              className="bg-white rounded-xl shadow-lg p-8 cursor-pointer transform hover:scale-105 transition-all duration-200 hover:shadow-xl border-2 border-transparent hover:border-indigo-300"
            >
              <div className="text-center">
                <div className="text-4xl mb-4">📚</div>
                <h3 className="text-2xl font-bold text-indigo-900 mb-3">Synonyms & Antonyms</h3>
                <p className="text-indigo-600 mb-4">Find words with similar or opposite meanings</p>
                <div className="bg-indigo-50 rounded-lg p-3">
                  <p className="text-sm text-indigo-700">
                    <strong>Example:</strong> What is a synonym for "abundant"?
                  </p>
                </div>
              </div>
            </div>

            <div 
              onClick={() => startGame('odd_one_out')}
              className="bg-white rounded-xl shadow-lg p-8 cursor-pointer transform hover:scale-105 transition-all duration-200 hover:shadow-xl border-2 border-transparent hover:border-green-300"
            >
              <div className="text-center">
                <div className="text-4xl mb-4">🔍</div>
                <h3 className="text-2xl font-bold text-green-900 mb-3">Odd One Out</h3>
                <p className="text-green-600 mb-4">Identify which word doesn't belong</p>
                <div className="bg-green-50 rounded-lg p-3">
                  <p className="text-sm text-green-700">
                    <strong>Example:</strong> Which doesn't belong: happy, joyful, sad, cheerful?
                  </p>
                </div>
              </div>
            </div>

            <div 
              onClick={() => startGame('analogies')}
              className="bg-white rounded-xl shadow-lg p-8 cursor-pointer transform hover:scale-105 transition-all duration-200 hover:shadow-xl border-2 border-transparent hover:border-purple-300"
            >
              <div className="text-center">
                <div className="text-4xl mb-4">🧩</div>
                <h3 className="text-2xl font-bold text-purple-900 mb-3">Analogies</h3>
                <p className="text-purple-600 mb-4">Complete word relationship patterns</p>
                <div className="bg-purple-50 rounded-lg p-3">
                  <p className="text-sm text-purple-700">
                    <strong>Example:</strong> Hot is to cold as light is to ___
                  </p>
                </div>
              </div>
            </div>
          </div>

          <div className="mt-12 text-center">
            <div className="bg-white rounded-xl shadow-lg p-6 max-w-2xl mx-auto">
              <h3 className="text-xl font-bold text-gray-800 mb-3">About This Quiz</h3>
              <p className="text-gray-600">
                Practice with 500 carefully selected vocabulary words from the 11+ curriculum. 
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
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-6">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="bg-white rounded-xl shadow-lg p-6 mb-8">
          <div className="flex justify-between items-center">
            <div className="flex items-center space-x-3">
              <span className="text-3xl">{config.icon}</span>
              <h1 className="text-2xl font-bold text-gray-900">
                {config.title}
              </h1>
            </div>
            <button
              onClick={backToMenu}
              className="bg-gray-500 hover:bg-gray-600 text-white px-4 py-2 rounded-lg transition-colors"
            >
              Back to Menu
            </button>
          </div>
        </div>

        {/* Score Display */}
        <div className="bg-white rounded-xl shadow-lg p-6 mb-8">
          <div className="flex justify-between items-center">
            <div className="flex space-x-8">
              <div className="text-center">
                <div className="text-2xl font-bold text-green-600">{score.correct}</div>
                <div className="text-sm text-gray-600">Correct</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-600">{score.total}</div>
                <div className="text-sm text-gray-600">Total</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-purple-600">{percentage}%</div>
                <div className="text-sm text-gray-600">Accuracy</div>
              </div>
            </div>
            <div className="text-right">
              <div className="text-sm text-gray-600">Words completed</div>
              <div className="text-lg font-semibold">{usedWords.size} / {words.length}</div>
            </div>
          </div>
        </div>

        {/* Question Card */}
        <div className="bg-white rounded-xl shadow-lg p-8 mb-8">
          <div className="text-center mb-8">
            <h2 className="text-2xl font-bold text-gray-800 mb-4">
              {currentQuestion.question}
            </h2>
            {currentQuestion.word && (
              <div className="text-lg text-gray-600 mb-6">
                Focus word: <span className="font-semibold text-indigo-700">{currentQuestion.word}</span>
              </div>
            )}
          </div>

          {/* Options */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8">
            {currentQuestion.options.map((option, index) => (
              <button
                key={index}
                onClick={() => handleAnswer(option)}
                disabled={feedback !== null}
                className={`p-4 rounded-lg border-2 transition-all duration-200 text-left ${
                  feedback === null
                    ? 'border-gray-300 hover:border-blue-400 hover:bg-blue-50'
                    : feedback.selectedAnswer === option
                    ? feedback.isCorrect
                      ? 'border-green-500 bg-green-50'
                      : 'border-red-500 bg-red-50'
                    : option === currentQuestion.correctAnswer
                    ? 'border-green-500 bg-green-50'
                    : 'border-gray-300 bg-gray-50'
                }`}
              >
                <div className="flex items-center space-x-3">
                  <div className={`w-8 h-8 rounded-full border-2 flex items-center justify-center text-sm font-bold ${
                    feedback === null
                      ? 'border-blue-400 text-blue-600'
                      : feedback.selectedAnswer === option
                      ? feedback.isCorrect
                        ? 'border-green-500 text-green-600 bg-green-100'
                        : 'border-red-500 text-red-600 bg-red-100'
                      : option === currentQuestion.correctAnswer
                      ? 'border-green-500 text-green-600 bg-green-100'
                      : 'border-gray-400 text-gray-600'
                  }`}>
                    {String.fromCharCode(65 + index)}
                  </div>
                  <span className="text-lg">{option}</span>
                  {feedback !== null && option === currentQuestion.correctAnswer && (
                    <span className="text-green-600 text-xl">✓</span>
                  )}
                  {feedback !== null && feedback.selectedAnswer === option && !feedback.isCorrect && (
                    <span className="text-red-600 text-xl">✗</span>
                  )}
                </div>
              </button>
            ))}
          </div>

          {/* Feedback */}
          {feedback && (
            <div className={`rounded-lg p-6 mb-6 ${
              feedback.isCorrect ? 'bg-green-50 border-l-4 border-green-400' : 'bg-red-50 border-l-4 border-red-400'
            }`}>
              <div className="flex items-center space-x-3 mb-3">
                <span className="text-2xl">
                  {feedback.isCorrect ? '🎉' : '📚'}
                </span>
                <h3 className={`text-xl font-bold ${
                  feedback.isCorrect ? 'text-green-800' : 'text-red-800'
                }`}>
                  {feedback.isCorrect ? 'Correct!' : 'Not quite right'}
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
                className="bg-blue-600 hover:bg-blue-700 text-white px-8 py-3 rounded-lg text-lg font-semibold transition-colors"
              >
                Next Question →
              </button>
            </div>
          )}
        </div>

        {/* Progress Indicator */}
        <div className="bg-white rounded-xl shadow-lg p-6">
          <div className="flex justify-between items-center mb-3">
            <span className="text-sm font-medium text-gray-600">Progress</span>
            <span className="text-sm text-gray-600">
              {usedWords.size} of {words.length} words practiced
            </span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-3">
            <div 
              className="bg-blue-500 h-3 rounded-full transition-all duration-500"
              style={{ width: `${(usedWords.size / words.length) * 100}%` }}
            ></div>
          </div>
          <div className="mt-3 text-center">
            <span className="text-xs text-gray-500">
              {((usedWords.size / words.length) * 100).toFixed(1)}% of vocabulary covered
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ElevenPlusQuizApp;