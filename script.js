const tarotDeck = [
  // Major Arcana
  { name: "Шут (0)", meaning: "Новое начало, спонтанность, вера во Вселенную. Пора сделать шаг в неизвестность.", tip: "Совет: рискните попробовать совершенно новое и не бойтесь показаться смешным сегодня." },
  { name: "Маг (I)", meaning: "Мастерство, сила воли, проявление желаемого. У вас есть все инструменты для успеха.", tip: "Совет: возьмите инициативу в свои руки. Сегодня вы можете убедить кого угодно в чем угодно." },
  { name: "Жрица (II)", meaning: "Интуиция, подсознание, скрытые истины. Доверьтесь своему внутреннему голосу.", tip: "Совет: не спешите с выводами. Прислушайтесь к интуиции и обращайте внимание на знаки." },
  { name: "Императрица (III)", meaning: "Изобилие, плодородие, забота и красота. Время роста и созидания.", tip: "Совет: проявите заботу о себе и близких. Окружите себя красотой и комфортом." },
  { name: "Император (IV)", meaning: "Власть, структура, стабильность. Необходима дисциплина для достижения цели.", tip: "Совет: наведите порядок в делах. Сегодня важны жесткая дисциплина и логика." },
  { name: "Иерофант (V)", meaning: "Традиции, духовный учитель, система верований. Путь к знаниям через established структуры.", tip: "Совет: следуйте правилам и традициям. Обратитесь за советом к более опытному человеку." },
  { name: "Влюбленные (VI)", meaning: "Любовь, гармония, важный выбор. Прислушайтесь к зову сердца.", tip: "Совет: делайте выбор сердцем, а не холодным расчетом. Проведите время с любимыми." },
  { name: "Колесница (VII)", meaning: "Победа, решимость, преодоление препятствий силой воли.", tip: "Совет: смело двигайтесь вперед, преодолевая любые сомнения. Удача на вашей стороне." },
  { name: "Сила (VIII)", meaning: "Внутренняя сила, мужество, сострадание. Победа над страхами через мягкость.", tip: "Совет: проявите мягкую настойчивость. Агрессия сегодня не поможет, действуйте с любовью." },
  { name: "Отшельник (IX)", meaning: "Поиск души, одиночество, внутреннее руководство. Время для рефлексии.", tip: "Совет: побудьте наедине со своими мыслями. Вам нужно время восстановить силы." },
  { name: "Колесо Фортуны (X)", meaning: "Удача, карма, поворотный момент. Судьба благосклонна к вам.", tip: "Совет: будьте готовы к неожиданным переменам и ловите удачу за хвост!" },
  { name: "Справедливость (XI)", meaning: "Правда, баланс, закон причин и следствий. Ваши решения определят исход.", tip: "Совет: будьте объективны и честны в своих поступках. Взвешивайте все 'за' и 'против'." },
  { name: "Повешенный (XII)", meaning: "Жертва, новый взгляд, отпускание ситуации. Пришло время посмотреть на вещи иначе.", tip: "Совет: посмотрите на ситуацию под другим углом. Временно отпустите контроль." },
  { name: "Смерть (XIII)", meaning: "Трансформация, конец одного цикла и начало нового. Необходимо отпустить прошлое.", tip: "Совет: смело отпускайте то, что изжило себя. Освободите место для нового." },
  { name: "Умеренность (XIV)", meaning: "Баланс, гармония, алхимия. Избегайте крайностей в ваших действиях.", tip: "Совет: избегайте любых крайностей. Ищите золотую середину во всех делах." },
  { name: "Дьявол (XV)", meaning: "Привязанность, искушение, теневая сторона. Освободитесь от того, что вас ограничивает.", tip: "Совет: не поддавайтесь сиюминутным искушениям и токсичным провокациям." },
  { name: "Башня (XVI)", meaning: "Внезапные изменения, разрушение иллюзий, пробуждение. То, что было ложным, рухнет.", tip: "Совет: не пытайтесь удержать то, что рушится. Разрушение расчистит путь к истине." },
  { name: "Звезда (XVII)", meaning: "Надежда, вдохновение, духовное исцеление. Впереди светлое будущее.", tip: "Совет: верьте в свою мечту и вдохновляйтесь! Сегодня прекрасный и светлый день." },
  { name: "Луна (XVIII)", meaning: "Иллюзии, страхи, подсознание. Не все является тем, чем кажется на первый взгляд.", tip: "Совет: не поддавайтесь надуманным страхам. Ситуация скоро прояснится сама." },
  { name: "Солнце (XIX)", meaning: "Радость, успех, позитив, жизненная сила. Блестящий результат.", tip: "Совет: наслаждайтесь жизнью! Проявите себя ярко и зарядите позитивом окружающих." },
  { name: "Суд (XX)", meaning: "Возрождение, внутренний зов, кармическое прощение. Время подведения итогов.", tip: "Совет: сделайте правильные выводы из прошлых ошибок и закройте старые долги." },
  { name: "Мир (XXI)", meaning: "Завершение, достижение, целостность. Вы находитесь там, где должны быть.", tip: "Совет: вы победитель. Расширяйте границы и наслаждайтесь чувством завершенности." }
];

// Minor Arcana Generation
const suits = [
  { name: 'Жезлов', gen: 'активные действия, энергию и преодоление препятствий.', love: 'много страсти, ярких эмоций и импульсивных поступков в отношениях.', car: 'амбициозные проекты, карьерный рост и необходимость проявлять инициативу.', tip: 'больше действуйте, проявляйте инициативу и не бойтесь быть в центре внимания!' },
  { name: 'Кубков', gen: 'сильные эмоции, интуицию и духовный поиск.', love: 'глубокие чувства, романтику, свидания и душевную близость.', car: 'приятную атмосферу в коллективе, творческий подход к задачам и работу по призванию.', tip: 'сегодня прислушивайтесь к сердцу, будьте открыты и дарите людям тепло.' },
  { name: 'Мечей', gen: 'логику, возможные конфликты и необходимость принимать жесткие решения.', love: 'период холодности, необходимость серьезного разговора или выяснения отношений умом, а не сердцем.', car: 'честную конкуренцию, интеллектуальный труд, но также возможные споры и стресс.', tip: 'отключите эмоции. Строго руководствуйтесь логикой, разумом и фактами.' },
  { name: 'Пентаклей', gen: 'материальную стабильность, здоровье и практичность.', love: 'надежные, серьезные намерения, желание строить совместный быт и фундамент.', car: 'стабильный доход, выгодные сделки и упорный труд, который обязательно окупится материально.', tip: 'будьте прагматичны, занимайтесь материальными делами и своим здоровьем.' }
];

const ranks = [
  { name: 'Туз', meaning: 'Это абсолютный новый потенциал, мощная искра и отличный старт для ваших начинаний.', tip: 'Совет: ловите шанс,' },
  { name: 'Двойка', meaning: 'Карта указывает на необходимость соблюдать баланс, искать компромисс или сделать важный выбор.', tip: 'Совет: ищите компромисс,' },
  { name: 'Тройка', meaning: 'Вас ждет рост, первые успешные результаты и радость от сотрудничества с другими.', tip: 'Совет: объединяйте усилия с другими,' },
  { name: 'Четверка', meaning: 'Это период стабильности, паузы, сохранения достигнутого. Время для отдыха и укрепления позиций.', tip: 'Совет: зафиксируйте свои позиции и отдохните,' },
  { name: 'Пятерка', meaning: 'Эта карта обычно предвещает временный кризис, конфликт интересов или непростое испытание.', tip: 'Совет: переоцените свои ресурсы,' },
  { name: 'Шестерка', meaning: 'Символ гармонии, помощи со стороны, либо возвращения к корням и прошлым приятным воспоминаниям.', tip: 'Совет: будьте благодарны за то что имеете,' },
  { name: 'Семерка', meaning: 'Время переоценки планов. Возможны иллюзии, скрытые мотивы или необходимость проявить хитрость.', tip: 'Совет: проявите максимальную хитрость и осторожность,' },
  { name: 'Восьмерка', meaning: 'Карта постоянного движения, оттачивания мастерства или кропотливого, но нужного труда.', tip: 'Совет: погрузитесь в монотонную работу,' },
  { name: 'Девятка', meaning: 'Близость к завершению. Возможен период удовлетворенности результатами, либо же внутренние страхи, если это мечи.', tip: 'Совет: опирайтесь только на себя,' },
  { name: 'Десятка', meaning: 'Кульминация ситуации, финальный аккорд. Завершение важного цикла или абсолютная полнота момента.', tip: 'Совет: подведите важные итоги этапа,' },
  { name: 'Паж', meaning: 'Ждите новостей или послания. Это также импульс к изучению чего-то совершенно нового.', tip: 'Совет: откройтесь новым знаниям и известиям,' },
  { name: 'Рыцарь', meaning: 'Стремительное развитие событий, движение вперед и готовность к действию.', tip: 'Совет: действуйте не раздумывая,' },
  { name: 'Королева', meaning: 'Зрелая женская энергия: владение ситуацией через заботу, интуицию или интеллект.', tip: 'Совет: действуйте мягко, по-женски гибко,' },
  { name: 'Король', meaning: 'Символ авторитета, лидерства, контроля над эмоциями и процессами вокруг вас.', tip: 'Совет: возьмите всю ответственность на себя,' }
];

// Combine Minor Arcana
suits.forEach(suit => {
  ranks.forEach(rank => {
    tarotDeck.push({
      name: `${rank.name} ${suit.name}`,
      meaning: `${rank.meaning} В целом, данная масть отражает ${suit.gen}`,
      love: `${rank.meaning} Если говорить о делах сердечных, масть предвещает ${suit.love}`,
      car: `${rank.meaning} В рабочих вопросах эта масть сулит ${suit.car}`,
      tip: `${rank.tip} ${suit.tip}`
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
const inputSection = document.getElementById('input-section');
const questionInput = document.getElementById('question-input');
const tarotCardContainer = document.querySelector('.tarot-card-container');
const tarotCard = document.getElementById('tarot-card');
const resultSection = document.getElementById('result-section');

const cardNameOverlay = document.getElementById('card-name-overlay');
const cardTitle = document.getElementById('card-title');
const cardMeaning = document.getElementById('card-meaning');

// New Feature Elements
const modeSelection = document.getElementById('mode-selection');
const modeQuestionBtn = document.getElementById('mode-question-btn');
const modeDailyBtn = document.getElementById('mode-daily-btn');
const modeThreeBtn = document.getElementById('mode-three-btn');
const backToModesBtn = document.getElementById('back-to-modes');
const backToModesBtn2 = document.getElementById('back-to-modes-2');
const backToModesBtn3 = document.getElementById('back-to-modes-3');
const dailyCardsSection = document.getElementById('daily-cards-section');
const threeReadingSection = document.getElementById('three-reading-section');
const drawThreeBtn = document.getElementById('draw-three-btn');
const threeResultSection = document.getElementById('three-result-section');
const miniCards = document.querySelectorAll('.tarot-card.mini');
const limitMessage = document.getElementById('limit-message');
const upsellPopup = document.getElementById('upsell-popup');
const closePopupBtn = document.getElementById('close-popup');

// Check URL param for Premium
const urlParams = new URLSearchParams(window.location.search);
const isPremium = urlParams.get('premium') === '1';

if (isPremium) {
  modeThreeBtn.classList.remove('hidden');
}

let upsellTimer = null;

// --- Limit Logic ---
function checkDailyLimit() {
  if (isPremium) return true;
  const today = new Date().toDateString();
  const usageData = JSON.parse(localStorage.getItem('tarotUsage')) || { date: '', count: 0 };
  
  if (usageData.date !== today) {
    usageData.date = today;
    usageData.count = 0;
    localStorage.setItem('tarotUsage', JSON.stringify(usageData));
  }
  return usageData.count < 3;
}

function incrementDailyUsage() {
  if (isPremium) return;
  const usageData = JSON.parse(localStorage.getItem('tarotUsage'));
  usageData.count += 1;
  localStorage.setItem('tarotUsage', JSON.stringify(usageData));
}

function initApp() {
  if (!checkDailyLimit()) {
    modeSelection.classList.add('hidden');
    limitMessage.classList.remove('hidden');
  }
}
initApp();

// --- Mode Switching ---
modeQuestionBtn.addEventListener('click', () => {
  modeSelection.style.opacity = '0';
  setTimeout(() => {
    modeSelection.classList.add('hidden');
    inputSection.classList.remove('hidden');
    // small delay for css transition
    setTimeout(() => { inputSection.style.opacity = '1'; }, 50);
  }, 300);
});

modeDailyBtn.addEventListener('click', () => {
  modeSelection.style.opacity = '0';
  setTimeout(() => {
    modeSelection.classList.add('hidden');
    dailyCardsSection.classList.remove('hidden');
    setTimeout(() => { dailyCardsSection.style.opacity = '1'; }, 50);
  }, 300);
});

if (isPremium) {
  modeThreeBtn.addEventListener('click', () => {
    modeSelection.style.opacity = '0';
    setTimeout(() => {
      modeSelection.classList.add('hidden');
      threeReadingSection.classList.remove('hidden');
      setTimeout(() => { threeReadingSection.style.opacity = '1'; }, 50);
    }, 300);
  });
}

[backToModesBtn, backToModesBtn2, backToModesBtn3].forEach(btn => {
  btn.addEventListener('click', () => {
    inputSection.classList.add('hidden');
    dailyCardsSection.classList.add('hidden');
    threeReadingSection.classList.add('hidden');
    modeSelection.classList.remove('hidden');
    modeSelection.style.opacity = '1';
    questionInput.value = '';
    
    // reset 3-card
    threeResultSection.classList.add('hidden');
    drawThreeBtn.style.display = 'block';
    for(let i=0; i<3; i++) {
        document.getElementById(`tc-${i}`).classList.remove('flipped');
    }
  });
});

closePopupBtn.addEventListener('click', () => {
  upsellPopup.classList.remove('show');
});

// --- Reading Logic ---
drawBtn.addEventListener('click', () => performReading('question'));

questionInput.addEventListener('keypress', function(e) {
  if (e.key === 'Enter') performReading('question');
});

miniCards.forEach(card => {
  card.addEventListener('click', () => {
    dailyCardsSection.style.opacity = '0';
    setTimeout(() => {
      dailyCardsSection.classList.add('hidden');
      performReading('daily');
    }, 300);
  });
});

function scheduleUpsell() {
  clearTimeout(upsellTimer);
  upsellTimer = setTimeout(() => {
    upsellPopup.classList.add('show');
  }, 20000); // 20 seconds
}

function performReading(mode = 'question') {
  if (!checkDailyLimit()) {
      alert("Энергия на сегодня иссякла 🌙 Приходите завтра!");
      return;
  }
  
  let userQuestion = "";
  let context = "general";
  
  if (mode === 'question') {
    userQuestion = questionInput.value.trim();
    if (userQuestion.length === 0) {
      questionInput.style.borderColor = 'red';
      questionInput.placeholder = "Пожалуйста, задайте вопрос...";
      setTimeout(() => { questionInput.style.borderColor = 'var(--gold)'; }, 1000);
      return;
    }
    context = analyzeContext(userQuestion);
    
    inputSection.style.opacity = '0';
    inputSection.style.transform = 'translateY(-20px)';
    setTimeout(() => { inputSection.classList.add('hidden'); }, 500);
  }

  incrementDailyUsage();
  
  setTimeout(() => {
    tarotCardContainer.classList.add('visible');
    
    const randomCard = tarotDeck[Math.floor(Math.random() * tarotDeck.length)];
    const cardText = randomCard.name;
    
    let meaningText = "";
    if (context === 'love') meaningText = randomCard.love ? randomCard.love : `В сфере отношений: ${randomCard.meaning}`;
    else if (context === 'career') meaningText = randomCard.car ? randomCard.car : `В финансовых делах: ${randomCard.meaning}`;
    else meaningText = randomCard.meaning;
    
    let answerHtml = "";
    if (mode === 'question') {
      const pfx = {
        love: ["На ваш вопрос о чувствах:", "В делах любовных:"],
        career: ["По поводу вашей работы:", "Ваша карьерная судьба шепчет:"],
        general: ["Карты говорят:", "Судьба отвечает вам:"]
      };
      const rs = pfx[context][Math.floor(Math.random() * pfx[context].length)];
      answerHtml = `<em>Ваш вопрос: "${userQuestion}"</em><br><br><strong>✨ ${rs}</strong><br>${meaningText}`;
    } else {
      answerHtml = `<strong>✨ Подсказка на день:</strong><br>${meaningText} <br><br><em>${randomCard.tip}</em>`;
    }
    
    setTimeout(() => {
      cardNameOverlay.innerText = cardText;
      tarotCard.classList.add('flipped');
      if (window.Telegram && window.Telegram.WebApp && window.Telegram.WebApp.HapticFeedback) {
          window.Telegram.WebApp.HapticFeedback.impactOccurred('medium');
      }
      
      setTimeout(() => {
        cardTitle.innerText = `Ваша карта: ${cardText}`;
        cardMeaning.innerHTML = answerHtml;
        resultSection.style.display = 'block';
        
        setTimeout(() => {
          resultSection.classList.add('visible');
          window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' });
          scheduleUpsell(); // Start the 20s timer
        }, 50);

      }, 1000); 
    }, 1500); 
  }, mode === 'question' ? 500 : 50); 
}

resetBtn.addEventListener('click', () => {
  resultSection.classList.remove('visible');
  tarotCard.classList.remove('flipped');
  clearTimeout(upsellTimer);
  
  setTimeout(() => {
    resultSection.style.display = 'none';
    tarotCardContainer.classList.remove('visible');
    
    questionInput.value = '';
    
    if (!checkDailyLimit()) {
      limitMessage.classList.remove('hidden');
    } else {
      modeSelection.classList.remove('hidden');
      modeSelection.style.opacity = '1';
    }
    
    setTimeout(() => { window.scrollTo({ top: 0, behavior: 'smooth' }); }, 50);
  }, 1000);
});

// --- Three Card Logic ---
drawThreeBtn.addEventListener('click', () => {
  drawThreeBtn.style.display = 'none';
  
  // pick 3 unique cards
  let deckCopy = [...tarotDeck];
  let picked = [];
  for(let i = 0; i < 3; i++) {
     let idx = Math.floor(Math.random() * deckCopy.length);
     picked.push(deckCopy[idx]);
     deckCopy.splice(idx, 1);
  }
  
  // Flip sequence
  picked.forEach((card, index) => {
      setTimeout(() => {
          document.getElementById(`tname-${index}`).innerText = card.name;
          document.getElementById(`tc-${index}`).classList.add('flipped');
          
          if (window.Telegram && window.Telegram.WebApp && window.Telegram.WebApp.HapticFeedback) {
              window.Telegram.WebApp.HapticFeedback.impactOccurred('medium');
          }
          
          if (index === 2) {
             setTimeout(() => {
                 document.getElementById('t-meaning-0').innerHTML = `<strong>Прошлое (${picked[0].name}):</strong><br>${picked[0].meaning}`;
                 document.getElementById('t-meaning-1').innerHTML = `<strong>Настоящее (${picked[1].name}):</strong><br>${picked[1].meaning}`;
                 document.getElementById('t-meaning-2').innerHTML = `<strong>Будущее (${picked[2].name}):</strong><br>${picked[2].meaning}`;
                 threeResultSection.classList.remove('hidden');
                 window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' });
             }, 1000);
          }
      }, index * 800);
  });
});
