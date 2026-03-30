const tarotDeck = [
  // Major Arcana
  { name: "Шут (0)", meaning: "Новое начало, спонтанность, вера во Вселенную. Пора сделать шаг в неизвестность." },
  { name: "Маг (I)", meaning: "Мастерство, сила воли, проявление желаемого. У вас есть все инструменты для успеха." },
  { name: "Жрица (II)", meaning: "Интуиция, подсознание, скрытые истины. Доверьтесь своему внутреннему голосу." },
  { name: "Императрица (III)", meaning: "Изобилие, плодородие, забота и красота. Время роста и созидания." },
  { name: "Император (IV)", meaning: "Власть, структура, стабильность. Необходима дисциплина для достижения цели." },
  { name: "Иерофант (V)", meaning: "Традиции, духовный учитель, система верований. Путь к знаниям через established структуры." },
  { name: "Влюбленные (VI)", meaning: "Любовь, гармония, важный выбор. Прислушайтесь к зову сердца." },
  { name: "Колесница (VII)", meaning: "Победа, решимость, преодоление препятствий силой воли." },
  { name: "Сила (VIII)", meaning: "Внутренняя сила, мужество, сострадание. Победа над страхами через мягкость." },
  { name: "Отшельник (IX)", meaning: "Поиск души, одиночество, внутреннее руководство. Время для рефлексии." },
  { name: "Колесо Фортуны (X)", meaning: "Удача, карма, поворотный момент. Судьба благосклонна к вам." },
  { name: "Справедливость (XI)", meaning: "Правда, баланс, закон причин и следствий. Ваши решения определят исход." },
  { name: "Повешенный (XII)", meaning: "Жертва, новый взгляд, отпускание ситуации. Пришло время посмотреть на вещи иначе." },
  { name: "Смерть (XIII)", meaning: "Трансформация, конец одного цикла и начало нового. Необходимо отпустить прошлое." },
  { name: "Умеренность (XIV)", meaning: "Баланс, гармония, алхимия. Избегайте крайностей в ваших действиях." },
  { name: "Дьявол (XV)", meaning: "Привязанность, искушение, теневая сторона. Освободитесь от того, что вас ограничивает." },
  { name: "Башня (XVI)", meaning: "Внезапные изменения, разрушение иллюзий, пробуждение. То, что было ложным, рухнет." },
  { name: "Звезда (XVII)", meaning: "Надежда, вдохновение, духовное исцеление. Впереди светлое будущее." },
  { name: "Луна (XVIII)", meaning: "Иллюзии, страхи, подсознание. Не все является тем, чем кажется на первый взгляд." },
  { name: "Солнце (XIX)", meaning: "Радость, успех, позитив, жизненная сила. Блестящий результат." },
  { name: "Суд (XX)", meaning: "Возрождение, внутренний зов, кармическое прощение. Время подведения итогов." },
  { name: "Мир (XXI)", meaning: "Завершение, достижение, целостность. Вы находитесь там, где должны быть." }
];

// Minor Arcana Generation
const suits = [
  { name: 'Жезлов', gen: 'активные действия, энергию и преодоление препятствий.', love: 'много страсти, ярких эмоций и импульсивных поступков в отношениях.', car: 'амбициозные проекты, карьерный рост и необходимость проявлять инициативу.' },
  { name: 'Кубков', gen: 'сильные эмоции, интуицию и духовный поиск.', love: 'глубокие чувства, романтику, свидания и душевную близость.', car: 'приятную атмосферу в коллективе, творческий подход к задачам и работу по призванию.' },
  { name: 'Мечей', gen: 'логику, возможные конфликты и необходимость принимать жесткие решения.', love: 'период холодности, необходимость серьезного разговора или выяснения отношений умом, а не сердцем.', car: 'честную конкуренцию, интеллектуальный труд, но также возможные споры и стресс.' },
  { name: 'Пентаклей', gen: 'материальную стабильность, здоровье и практичность.', love: 'надежные, серьезные намерения, желание строить совместный быт и фундамент.', car: 'стабильный доход, выгодные сделки и упорный труд, который обязательно окупится материально.' }
];

const ranks = [
  { name: 'Туз', meaning: 'Это абсолютный новый потенциал, мощная искра и отличный старт для ваших начинаний.' },
  { name: 'Двойка', meaning: 'Карта указывает на необходимость соблюдать баланс, искать компромисс или сделать важный выбор.' },
  { name: 'Тройка', meaning: 'Вас ждет рост, первые успешные результаты и радость от сотрудничества с другими.' },
  { name: 'Четверка', meaning: 'Это период стабильности, паузы, сохранения достигнутого. Время для отдыха и укрепления позиций.' },
  { name: 'Пятерка', meaning: 'Эта карта обычно предвещает временный кризис, конфликт интересов или непростое испытание.' },
  { name: 'Шестерка', meaning: 'Символ гармонии, помощи со стороны, либо возвращения к корням и прошлым приятным воспоминаниям.' },
  { name: 'Семерка', meaning: 'Время переоценки планов. Возможны иллюзии, скрытые мотивы или необходимость проявить хитрость.' },
  { name: 'Восьмерка', meaning: 'Карта постоянного движения, оттачивания мастерства или кропотливого, но нужного труда.' },
  { name: 'Девятка', meaning: 'Близость к завершению. Возможен период удовлетворенности результатами, либо же внутренние страхи, если это мечи.' },
  { name: 'Десятка', meaning: 'Кульминация ситуации, финальный аккорд. Завершение важного цикла или абсолютная полнота момента.' },
  { name: 'Паж', meaning: 'Ждите новостей или послания. Это также импульс к изучению чего-то совершенно нового.' },
  { name: 'Рыцарь', meaning: 'Стремительное развитие событий, движение вперед и готовность к действию.' },
  { name: 'Королева', meaning: 'Зрелая женская энергия: владение ситуацией через заботу, интуицию или интеллект.' },
  { name: 'Король', meaning: 'Символ авторитета, лидерства, контроля над эмоциями и процессами вокруг вас.' }
];

// Combine Minor Arcana
suits.forEach(suit => {
  ranks.forEach(rank => {
    tarotDeck.push({
      name: `${rank.name} ${suit.name}`,
      meaning: `${rank.meaning} В целом, данная масть отражает ${suit.gen}`,
      love: `${rank.meaning} Если говорить о делах сердечных, масть предвещает ${suit.love}`,
      car: `${rank.meaning} В рабочих вопросах эта масть сулит ${suit.car}`
    });
  });
});

function analyzeContext(question) {
  const q = question.toLowerCase();
  if (/(люб|отношен|мужчин|девушк|встреч|замуж|жен|чувств|бывш|измен|сойдемся|вместе|брак)/i.test(q)) {
    return 'love';
  } else if (/(работ|карьер|деньг|финанс|бизнес|увол|начал|зарплат|долг|сделк)/i.test(q)) {
    return 'career';
  } else {
    return 'general';
  }
}

// Select Elements
const drawBtn = document.getElementById('draw-btn');
const resetBtn = document.getElementById('reset-btn');
const inputSection = document.querySelector('.input-section');
const questionInput = document.getElementById('question-input');
const tarotCardContainer = document.querySelector('.tarot-card-container');
const tarotCard = document.getElementById('tarot-card');
const resultSection = document.getElementById('result-section');

const cardNameOverlay = document.getElementById('card-name-overlay');
const cardTitle = document.getElementById('card-title');
const cardMeaning = document.getElementById('card-meaning');

drawBtn.addEventListener('click', performReading);

questionInput.addEventListener('keypress', function(e) {
  if (e.key === 'Enter') {
    performReading();
  }
});

function performReading() {
  const userQuestion = questionInput.value.trim();
  if (userQuestion.length === 0) {
    questionInput.style.borderColor = 'red';
    questionInput.placeholder = "Пожалуйста, задайте вопрос...";
    setTimeout(() => { questionInput.style.borderColor = 'var(--gold)'; }, 1000);
    return;
  }

  const context = analyzeContext(userQuestion);

  inputSection.style.opacity = '0';
  inputSection.style.transform = 'translateY(-20px)';
  
  setTimeout(() => {
    inputSection.classList.add('hidden');
    inputSection.style.display = 'none';
    
    tarotCardContainer.classList.add('visible');
    
    const randomCard = tarotDeck[Math.floor(Math.random() * tarotDeck.length)];
    const cardText = randomCard.name;
    
    // Format response based on context
    let meaningText = "";
    if (context === 'love') {
      meaningText = randomCard.love ? randomCard.love : `В сфере отношений и чувств эта карта говорит о следующем: ${randomCard.meaning}`;
    } else if (context === 'career') {
      meaningText = randomCard.car ? randomCard.car : `В финансовых и рабочих делах эта карта указывает на: ${randomCard.meaning}`;
    } else {
      meaningText = randomCard.meaning;
    }
    
    const contextPrefixes = {
      love: ["На ваш вопрос о чувствах карты отвечают:", "В делах любовных Вселенная говорит:"],
      career: ["По поводу вашей работы и финансов:", "Ваша денежная и карьерная судьба шепчет:"],
      general: ["Карты говорят:", "Тайный знак указывает:", "Судьба отвечает вам:"]
    };
    const prefixArray = contextPrefixes[context];
    const rs = prefixArray[Math.floor(Math.random() * prefixArray.length)];
    
    setTimeout(() => {
      cardNameOverlay.innerText = cardText;
      tarotCard.classList.add('flipped');
      
      setTimeout(() => {
        cardTitle.innerText = `Ваша карта: ${cardText}`;
        cardMeaning.innerHTML = `<em>Ваш вопрос: "${userQuestion}"</em><br><br><strong>✨ ${rs}</strong><br>${meaningText}`;
        
        resultSection.style.display = 'block';
        setTimeout(() => {
          resultSection.classList.add('visible');
          window.scrollTo({
             top: document.body.scrollHeight,
             behavior: 'smooth'
          });
        }, 50);

      }, 1000); 
    }, 1500); 
  }, 500); 
}

resetBtn.addEventListener('click', () => {
  // Hide results and un-flip card
  resultSection.classList.remove('visible');
  tarotCard.classList.remove('flipped');
  
  setTimeout(() => {
    resultSection.style.display = 'none';
    tarotCardContainer.classList.remove('visible');
    
    // Reset inputs
    questionInput.value = '';
    inputSection.style.display = 'flex';
    inputSection.classList.remove('hidden');
    
    setTimeout(() => {
      inputSection.style.opacity = '1';
      inputSection.style.transform = 'translateY(0)';
      window.scrollTo({
             top: 0,
             behavior: 'smooth'
          });
    }, 50);
  }, 1000);
});
