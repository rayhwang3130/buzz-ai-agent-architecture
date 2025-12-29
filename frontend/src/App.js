import React, { useState } from 'react';
import Header from './components/Header';
import ChatWindow from './components/ChatWindow';
import ChatInput from './components/ChatInput';
import Sidebar from './components/Sidebar';

function arrayToHtmlTable(data) {
  if (!data || data.length === 0) return '';
  let table = '<table style="width: 100%; border-collapse: collapse; margin-top: 10px;">';
  // Header
  table += '<thead><tr>';
  data[0].forEach(header => {
    table += `<th style="border: 1px solid #ddd; padding: 8px; text-align: left; background-color: #f2f2f2; color: #333;">${header}</th>`;
  });
  table += '</tr></thead>';
  // Body
  table += '<tbody>';
  data.slice(1).forEach(row => {
    table += '<tr>';
    row.forEach(cell => {
      table += `<td style="border: 1px solid #ddd; padding: 8px;">${cell}</td>`;
    });
    table += '</tr>';
  });
  table += '</tbody></table>';
  return table;
}

const qaPairs = [
  {
    question: "UNPK+48H의 총 버즈량, Galaxy AI 버즈량, S25 Ultra 및 Base/+의 버즈량을 표로 정리해줘.",
    explanation: "UNPK 48시간동안 발생한 총 버즈량 및 Galaxy AI, 제품 별 버즈량은 다음과 같습니다. Galaxy AI와 S25 Ultra의 버즈량이 크게 증가하였음을 알 수 있습니다.",
    data: [
      ['항목', '총 버즈량', 'Galaxy AI', 'S25 Familiy', 'S25 Ultra', 'S25 Base/+'],
      ['버즈량', '4.0M', '3.2M', '2.4M', '1.7M', '534K'],
      ['YoY', 'x1.2', 'x1.9', 'x1.3', 'x2.4', 'x0.6'],
    ],
  },
  {
    question: "소비자 버즈량 및 비중 예시",
    explanation: "UNPK 48시간동안 발생한 소비자 버즈량 및 비중은 다음과 같습니다.",
    data: [
      ['총 버즈량', '소비자 버즈량', '비중'],
      ['3.4M', '235K', '6.9%'],
    ],
  },
  {
    question: "UNPK+48H 동안 S25 Ultra와 S25 Base/+의 기능 별 언급 순위, 버즈량 및 비중을 알려줘.",
    explanation: "UNPK 48시간동안 2가지 제품에 대해 발생한 기능 별 버즈량 및 비중 순위는 다음과 같습니다. S25 Ultra는 AI, Camera, Game 기능이 주로 언급되었고, S25 Base/+는 AI와 Design 기능이 많이 언급되었습니다.",
    data: [
      ['순위', 'S25 Ultra', '버즈량', '비중', 'S25 Base/+', '버즈량', '비중'],
      ['1', 'AI', '1.4M', '65%', 'AI', '322K', '57%'],
      ['2', 'Camera', '228K', '11%', 'Design', '45K', '8%'],
      ['3', 'Game', '187K', '9%', 'AP/Memory', '39K', '7%'],
      ['4', 'Design', '92K', '5%', 'Price', '28K', '5%'],
      ['5', 'AP/Memory', '59K', '3%', 'Camera', '26K', '5%'],
    ],
  },
  {
    question: "그러면 UNPK+48H 동안 S25 Ultra와 S25 Base/+의 기능 별 긍정 버즈량 순위 및 비중을 알려줄래?",
    explanation: "UNPK 48시간동안 2가지 제품에 대해 발생한 기능 별 긍정 비중 순위는 다음과 같습니다. S25 Ultra는 Design, AP/Memory, Durability 기능이 주로 긍정적으로 언급되었고, S25 Base/+는 AP/Memory와 Design 기능이 많이 긍정적으로 언급되었습니다.",
    data: [
      ['순위', 'S25 Ultra', '버즈량', '비중', '긍정 비중', '부정 비중', 'S25 Base/+', '버즈량', '비중', '긍정 비중', '부정 비중'],
      ['1', 'Design', '92K', '4%', '24%', '5%', 'AP/Memory', '39K', '7%', '44%', '2%'],
      ['2', 'AP/Memory', '59K', '3%', '19%', '6%', 'Design', '45K', '8%', '20%', '7%'],
      ['3', 'Durability', '28K', '1%', '18%', '6%', 'AI', '322K', '57%', '14%', '0%'],
      ['4', 'Display', '38K', '2%', '17%', '5%', 'Game', '14K', '3%', '14%', '7%'],
      ['5', 'Battery', '29K', '1%', '15%', '10%', 'Camera', '26K', '5%', '13%', '7%'],
    ],
  },
  {
    question: "S25 Ultra의 Design에 대해 긍정적으로 반응한 주된 이유가 뭐야?",
    text: "<div style='background-color: #e0f7fa; padding: 10px; border-radius: 5px; margin-bottom: 10px;'>" +
      "  <p>S25 Ultra의 디자인에 대한 긍정적인 반응은 주로 <strong>'둥근 모서리 디자인'</strong>과 <strong>'깔끔한 색상'</strong>에 대한 호평 때문입니다. 이러한 디자인 요소들이 사용자들에게 편안함과 시각적인 만족감을 제공했습니다.</p>" +
      "</div>" +
      "<p>아래는 이에 대한 사용자들의 구체적인 반응 예시입니다:</p>" +
      "<ul>" +
      "  <li><strong>둥근 모서리 디자인:</strong> 기존 S23 Ultra의 각진 모서리 디자인이 손에 통증을 유발한다는 의견이 있었으나, S25 Ultra에서는 둥근 모서리로 변경되어 그립감이 향상되고 장시간 사용 시의 피로감이 줄어들었다는 점에서 좋은 평가를 받고 있습니다. <br/><em>\"Finally, curved edges on the S25 Ultra, my hands were literally aching using the S23 Ultra all this time...\"</em></li>" +
      "  <li><strong>깔끔한 색상:</strong> 이번 S25 Ultra의 실버 색상은 고급스러우면서도 깔끔한 느낌을 주어, 사용자들로 하여금 개인적으로 소장하고 싶을 만큼 매력적이라는 평가를 이끌어내고 있습니다. <br/><em>\"The silver color looks really nice on the Galaxy S25 Ultra, thinking of getting one myself.\"</em></li>" +
      "</ul>"
  },
  {
    question: "그럼 S25 Ultra의 AP/Memory에 대해서는 긍정적으로 반응한 주된 이유가 뭐야?",
    text: "<div style='background-color: #e0f7fa; padding: 10px; border-radius: 5px; margin-bottom: 10px;'>" +
      "  <p>S25 Ultra의 AP/Memory에 대한 긍정적인 반응은 <strong>'Snapdragon 8 Elite 탑재'</strong>로 인한 <strong>'성능 향상 기대감'</strong> 때문입니다. 새로운 AP가 제공할 뛰어난 게이밍 경험과 전반적인 사용성 개선에 대한 기대가 큽니다.</p>" +
      "</div>" +
      "<p>아래는 이에 대한 사용자들의 구체적인 반응 예시입니다:</p>" +
      "<ul>" +
      "  <li><strong>최적화된 게이밍 경험:</strong> 최신 AP인 Snapdragon 8 Elite가 탑재됨에 따라, 고사양을 요구하는 게임들도 끊김 없이 부드럽게 즐길 수 있을 것이라는 기대감이 형성되고 있습니다. 이는 게이머들에게 매우 긍정적인 신호로 받아들여지고 있습니다. <br/><em>\"Enjoy perfect gameplay on the Galaxy S25 Ultra, powered by the Snapdragon 8 Elite.\"</em></li>" +
      "  <li><strong>향상된 사용자 경험:</strong> 단순히 게임 성능뿐만 아니라, 앱 구동 속도, 멀티태스킹 능력 등 전반적인 기기 사용 경험이 Snapdragon 8 Elite로 인해 크게 향상될 것이라는 긍정적인 전망이 지배적입니다. <br/><em>\"Snapdragon 8 Elite brings enhanced experience to Galaxy S25 Ultra users\"</em></li>" +
      "</ul>"
  },
  {
    question: "S25 Ultra의 디자인 관련 언급 중에서, 폼팩터와 관련된 버즈량 및 비중은 어떻게 돼?",
    text: "<div style='background-color: #e0f7fa; padding: 10px; border-radius: 5px; margin-bottom: 10px;'>" +
      "  <p>현재 디자인 언급 중에서 '폼팩터'의 정확한 버즈량 및 비중은 파악할 수 없어요. 하지만 디자인 관련 언급 92K 중 폼팩터와 관련된 내용은 아래와 같습니다:</p>" +
      "</div>" +
      "<p>아래는 폼팩터 관련 사용자 반응 예시입니다:</p>" +
      "<ul>" +
      "  <li><strong>슬림한 디자인:</strong> S25 Ultra의 새로운 슬림 디자인은 전작 대비 무게감을 덜어내어, 사용자들이 더욱 편안하고 가볍게 기기를 사용할 수 있게 합니다. 이는 장시간 사용에도 부담을 줄여주는 긍정적인 요소로 평가받고 있습니다. <br/><em>\"The new slim design makes it feel lighter in hand.\"</em></li>" +
      "  <li><strong>확장된 화면:</strong> S25 Ultra의 확장된 화면 크기는 미디어 소비 경험을 크게 향상시킵니다. 동영상 시청이나 게임 플레이 시 몰입감을 높여주며, 더 넓은 시야를 제공하여 사용자 만족도를 높이는 핵심 요소로 작용합니다. <br/><em>\"I prefer the bigger screen size for media consumption.\"</em></li>" +
      "</ul>"
  },
  {
    question: "S25 Ultra의 디자인에 대하여 주요 긍정 언급은 어떤게 있어?",
    text: "<div style='background-color: #e0f7fa; padding: 10px; border-radius: 5px; margin-bottom: 10px;'>" +
      "  <p>디자인에 대한 주요 긍정 언급에 대해 정확하게 버즈량 및 비중을 파악할 수 없지만, 소비자들은 아래와 관련된 이야기를 했어요:</p>" +
      "</div>" +
      "<ul>" +
      "  <li><strong>색상:</strong> 이번 S25 Ultra에 새롭게 추가된 티타늄 색상 라인업은 사용자들에게 고급스럽고 세련된 이미지를 선사하며 큰 호응을 얻고 있습니다. 특히, 빛에 따라 미묘하게 변화하는 색감은 기존 모델과 차별화되는 포인트로 긍정적인 평가를 받고 있습니다. <br/><em>\"The new titanium color options are so premium.\"</em></li>" +
      "  <li><strong>무게:</strong> S25 Ultra는 전작 대비 경량화에 성공하여, 사용자들이 체감할 수 있을 정도로 가벼워졌다는 평가가 많습니다. 이는 휴대성을 높이고 장시간 사용 시 손목의 피로를 줄여주어 사용자 편의성을 크게 개선한 부분입니다. <br/><em>\"It feels noticeably lighter than the S24 Ultra, making it much more comfortable to hold.\"</em></li>" +
      "  <li><strong>얇기:</strong> 기기의 두께가 얇아지면서 주머니나 가방에 보관하기 용이해졌으며, 한 손에 쥐었을 때의 그립감 또한 향상되었습니다. 이러한 슬림한 디자인은 현대적인 미학을 만족시키는 동시에 실용성까지 겸비했다는 점에서 좋은 반응을 얻고 있습니다. <br/><em>\"So much thinner! It fits perfectly in my pocket now.\"</em></li>" +
      "</ul>"
  },
  {
    question: "S25 Ultra의 디자인 관련 언급 중에서, 폼팩터와 관련된 버즈량 및 비중을 자세히 알려줘.",
    text: "<div style='background-color: #e0f7fa; padding: 10px; border-radius: 5px; margin-bottom: 10px;'><p>디자인 관련 언급 92K 중 폼팩터와 관련된 주요 내용은 아래와 같습니다:</p></div>" +
      "<table style='width: 100%; border-collapse: collapse; margin-top: 10px;'><thead><tr><th style='border: 1px solid #ddd; padding: 8px; text-align: left; background-color: #f2f2f2; color: #333;'>주요 원인</th><th style='border: 1px solid #ddd; padding: 8px; text-align: left; background-color: #f2f2f2; color: #333;'>버즈량</th><th style='border: 1px solid #ddd; padding: 8px; text-align: left; background-color: #f2f2f2; color: #333;'>비중</th></tr></thead><tbody><tr><td style='border: 1px solid #ddd; padding: 8px;'>슬림한 디자인</td><td style='border: 1px solid #ddd; padding: 8px;'>30K</td><td style='border: 1px solid #ddd; padding: 8px;'>33%</td></tr><tr><td style='border: 1px solid #ddd; padding: 8px;'>확장된 화면</td><td style='border: 1px solid #ddd; padding: 8px;'>25K</td><td style='border: 1px solid #ddd; padding: 8px;'>27%</td></tr></tbody></table>" +
      "<p><strong>슬림한 디자인:</strong> S25 Ultra의 새로운 슬림 디자인은 전작 대비 무게감을 덜어내어, 사용자들이 더욱 편안하고 가볍게 기기를 사용할 수 있게 합니다. 이는 장시간 사용에도 부담을 줄여주는 긍정적인 요소로 평가받고 있습니다.</p>" +
      "<p>아래는 폼팩터 관련 사용자 반응 예시입니다:</p>" +
      "<ul>" +
      "  <li><em>\"The new slim design makes it feel lighter in hand.\"</em></li>" +
      "</ul>" +
      "<p><strong>확장된 화면:</strong> S25 Ultra의 확장된 화면 크기는 미디어 소비 경험을 크게 향상시킵니다. 동영상 시청이나 게임 플레이 시 몰입감을 높여주며, 더 넓은 시야를 제공하여 사용자 만족도를 높이는 핵심 요소로 작용합니다.</p>" +
      "<p>아래는 폼팩터 관련 사용자 반응 예시입니다:</p>" +
      "<ul>" +
      "  <li><em>\"I prefer the bigger screen size for media consumption.\"</em></li>" +
      "</ul>"
  },
  // {
  //   question: "반대로, UNPK+48H 동안 S25 Ultra와 S25 Base/+의 기능 별 부정 버즈량 순위 및 비중은 어떻게 돼?",
  //   explanation: "UNPK 48시간동안 2가지 제품에 대해 발생한 기능 별 부정 버즈량 및 비중 순위는 다음과 같습니다. S25 Ultra는 AI, Design, AP/Memory 기능이 주로 부정적으로 언급되었고, S25 Base/+는 Design과 Price 기능이 많이 부정적으로 언급되었습니다.",
  //   data: [ 
  //     ['순위', 'S25 Ultra', '버즈량', '비중', '긍정 비중', '부정 비중', 'S25 Base/+', '버즈량', '비중', '긍정 비중', '부정 비중'],
  //     ['1', 'S-Pen', '15K', '1%', '8%', '15%', 'Audio', '8K', '1%', '6%', '15%'],
  //     ['2', 'Battery', '29K', '1%', '15%', '10%', 'UI/UX', '19K', '3%', '10%', '13%'],
  //     ['3', 'Price', '37K', '2%', '10%', '9%', 'Battery', '16K', '3%', '13%', '11%'],
  //     ['4', 'AP/Memory', '59K', '3%', '19%', '6%', 'Price', '28K', '5%', '3%', '9%'],
  //     ['5', 'Durability', '28K', '1%', '18%', '6%', 'Design', '45K', '8%', '20%', '7%'],
  //   ],
  // },
  // {
  //   question: "S-Pen에 대하여 부정적으로 반응한 이유가 뭐야?",
  //   text: "S25 Ultra의 S-Pen에 대해 부정적으로 언급한 주요 이유는 다음과 같습니다: 1) S-Pen의 Bluetooth 기능 삭제 2) S-Pen의 그립감 및 사용감 불편 3) S-Pen 기능 제한 및 호환성 문제",
  // },
  // {
  //   question: "UNPK+48시간 동안, 소비자들이 언급한 S25 Ultra 및 S25 Base/+의 기능 언급량 순위 및 비중은 어때?",
  //   explanation: "UNPK 48시간동안 2가지 제품에 대해 소비자들이 언급한 기능 별 버즈량 및 비중 순위는 다음과 같습니다. S25 Ultra는 AI, Camera, Game 기능이 주로 언급되었고, S25 Base/+는 Design과 AP/Memory 기능이 많이 언급되었습니다.",
  //   data: [ 
  //     ['순위', 'S25 Ultra', '버즈량', '비중', 'S25 Base/+', '버즈량', '비중'],
  //     ['1', 'AI', '1.7M', '62%', 'Design', '61K', '26%'],
  //     ['2', 'Camera', '259K', '9%', 'AP/Memory', '30K', '13%'],
  //     ['3', 'Game', '202K', '7%', 'Price', '28K', '12%'],
  //     ['4', 'Design', '155K', '6%', 'Camera', '26K', '11%'],
  //     ['5', 'AP/Memory', '103K', '4%', 'Battery', '24K', '10%'],
  //   ],
  // }
];


function App() {
  const [messages, setMessages] = useState([
    { text: 'Hello! How can I help you today?', sender: 'bot' }
  ]);
  const [history, setHistory] = useState([
    'Previous conversation 1',
    'Another past chat',
  ]);
  const [isTyping, setIsTyping] = useState(false);

  const handleSendMessage = (text) => {
    const newMessage = { text, sender: 'user' };
    const newMessages = [...messages, newMessage];
    setMessages(newMessages);
    setIsTyping(true);

    const minDelay = 1000;
    const maxDelay = 2000;
    const randomDelay = Math.floor(Math.random() * (maxDelay - minDelay + 1)) + minDelay;

    setTimeout(() => {
      const matchedQa = qaPairs.find(qa => qa.question === text);

      let botResponse;

      if (matchedQa) {
        let responseText = "";
        if (matchedQa.data) {
          // Add styled explanation if it exists
          if (matchedQa.explanation) {
            responseText += `<div style='background-color: #e0f7fa; padding: 10px; border-radius: 5px; margin-bottom: 10px;'>${matchedQa.explanation}</div>`;
          }

          const headerRow = matchedQa.data[0];
          if (headerRow.includes('S25 Ultra') && headerRow.includes('S25 Base/+') && headerRow[0] === '순위') {
            const ultraIndex = headerRow.indexOf('S25 Ultra');
            const baseIndex = headerRow.indexOf('S25 Base/+');

            // For S25 Ultra table
            const table1Header = headerRow.slice(0, baseIndex);
            const table1Data = [
              table1Header,
              ...matchedQa.data.slice(1).map(row => row.slice(0, baseIndex))
            ];

            // For S25 Base/+ table
            const table2Header = [headerRow[0], ...headerRow.slice(baseIndex)];
            const table2Data = [
              table2Header,
              ...matchedQa.data.slice(1).map(row => [row[0], ...row.slice(baseIndex)])
            ];

            responseText += `<h3>S25 Ultra</h3>${arrayToHtmlTable(table1Data)}`;
            responseText += `<h3>S25 Base/+</h3>${arrayToHtmlTable(table2Data)}`;

          } else {
            responseText += arrayToHtmlTable(matchedQa.data);
          }

          botResponse = {
            text: responseText,
            sender: 'bot',
          };

        } else if (matchedQa.text) {
          botResponse = {
            text: matchedQa.text,
            sender: 'bot',
          };
        }
      } else {
        botResponse = {
          text: "해당 데이터를 찾지 못하였습니다. 다른 질문을 해주시겠어요?",
          sender: 'bot',
        };
      }

      setMessages([...newMessages, botResponse]);
      setIsTyping(false);
    }, randomDelay);
  };

  const handleClearHistory = () => {
    setHistory([]);
    setMessages([{ text: '안녕하세요, 무엇을 도와드릴까요?', sender: 'bot' }]);
  };

  const handleNewChat = () => {
    setMessages([{ text: '안녕하세요, 무엇을 도와드릴까요?', sender: 'bot' }]);
  };

  return (
    <div className="App">
      <div className="App-body">
        <Sidebar history={history} onClearHistory={handleClearHistory} onNewChat={handleNewChat} />
        <div className="main-content">
          <Header />
          <div className="chat-container">
            <ChatWindow messages={messages} isTyping={isTyping} />
            <ChatInput onSendMessage={handleSendMessage} />
          </div>
        </div>
      </div>
      <footer style={{ textAlign: 'center', padding: '10px', fontSize: '0.8em', color: '#777', backgroundColor: '#f0f4f9' }}>
        This is Demo UI, and the Agent AI can make mistakes.
      </footer>
    </div>
  );
}

export default App;