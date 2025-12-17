import dotenv from 'dotenv';
import OpenAI from 'openai';
import { AcontextClient } from '@acontext/acontext';

dotenv.config();

// Initialize Acontext client
const acontextClient = new AcontextClient({
  apiKey: process.env.ACONTEXT_API_KEY || 'sk-ac-your-root-api-bearer-token',
  baseUrl: process.env.ACONTEXT_BASE_URL || 'http://localhost:8029/api/v1',
  timeout: 60000,
});

// Tool definitions
const tools = [
  {
    type: 'function' as const,
    function: {
      name: 'get_weather',
      description: 'Returns weather info for the specified city.',
      parameters: {
        type: 'object',
        properties: {
          city: {
            type: 'string',
            description: 'The city to get weather for',
          },
        },
        required: ['city'],
        additionalProperties: false,
      },
    },
  },
  {
    type: 'function' as const,
    function: {
      name: 'book_flight',
      description: 'Book a flight.',
      parameters: {
        type: 'object',
        properties: {
          from_city: {
            type: 'string',
            description: 'The departure city',
          },
          to_city: {
            type: 'string',
            description: 'The destination city',
          },
          date: {
            type: 'string',
            description: 'The date of the flight',
          },
        },
        required: ['from_city', 'to_city', 'date'],
        additionalProperties: false,
      },
    },
  },
];

// Tool implementations
function getWeather(city: string): string {
  return `The weather in ${city} is sunny`;
}

function bookFlight(fromCity: string, toCity: string, date: string): string {
  return `Flight booked successfully for '${fromCity}' to '${toCity}' on '${date}'`;
}

function executeTool(toolName: string, toolArgs: Record<string, any>): string {
  if (toolName === 'get_weather') {
    return getWeather(toolArgs.city);
  } else if (toolName === 'book_flight') {
    return bookFlight(toolArgs.from_city, toolArgs.to_city, toolArgs.date);
  } else {
    return `Unknown tool: ${toolName}`;
  }
}

function createOpenAIClient(): OpenAI {
  const baseUrl = process.env.OPENAI_BASE_URL || undefined;
  return new OpenAI({
    apiKey: process.env.OPENAI_API_KEY,
    baseURL: baseUrl,
  });
}

async function appendMessage(
  message: any,
  conversation: any[],
  sessionId: string
): Promise<any[]> {
  conversation.push(message);
  await acontextClient.sessions.storeMessage(sessionId, message, {
    format: 'openai',
  });
  return conversation;
}

async function runAgent(
  client: OpenAI,
  conversation: any[]
): Promise<[string, any[]]> {
  const messagesToSend: any[] = [
    { role: 'system', content: 'You are a helpful assistant' },
    ...conversation,
  ];

  const newMessages: any[] = [];
  const maxIterations = 10;
  let iteration = 0;
  let finalContent = '';

  while (iteration < maxIterations) {
    iteration += 1;

    // Call OpenAI API
    const response = await client.chat.completions.create({
      model: 'gpt-4o-mini',
      messages: messagesToSend,
      tools: tools,
      tool_choice: 'auto',
    });

    const message = response.choices[0].message;

    // Convert message to dict format
    const messageDict: any = {
      role: message.role,
      content: message.content,
    };

    // Handle tool calls
    // Store tool call info with function details for later execution
    const toolCallsWithFunction: Array<{
      id: string;
      function: { name: string; arguments: string };
    }> = [];

    if (message.tool_calls) {
      messageDict.tool_calls = message.tool_calls.map((tc: any) => {
        // Store function info for execution
        toolCallsWithFunction.push({
          id: tc.id,
          function: {
            name: tc.function.name,
            arguments: tc.function.arguments,
          },
        });

        return {
          id: tc.id,
          type: 'function',
          function: {
            name: tc.function.name,
            arguments: tc.function.arguments,
          },
        };
      });
    }

    messagesToSend.push(messageDict);
    newMessages.push(messageDict);

    // If there are no tool calls, we're done
    if (!message.tool_calls || message.tool_calls.length === 0) {
      finalContent = message.content || '';
      break;
    }

    // Execute tool calls using the stored function info
    for (const toolCallInfo of toolCallsWithFunction) {
      const functionName = toolCallInfo.function.name;
      const functionArgsStr = toolCallInfo.function.arguments || '{}';
      const functionArgs = JSON.parse(functionArgsStr);

      // Execute the function
      const functionResult = executeTool(functionName, functionArgs);

      // Add tool response to messages
      const toolMessage = {
        role: 'tool' as const,
        tool_call_id: toolCallInfo.id,
        content: functionResult,
      };
      messagesToSend.push(toolMessage);
      newMessages.push(toolMessage);
    }
  }

  return [finalContent, newMessages];
}

async function session1(sessionId: string): Promise<void> {
  const client = createOpenAIClient();

  // Build conversation history using OpenAI message format
  // This format works with both OpenAI and Acontext
  let conversation: any[] = [];

  // First interaction - ask for trip plan
  console.log('\n=== First interaction: Planning trip ===');
  const userMsg1 = {
    role: 'user',
    content:
      "I'd like to have a 3-day trip in Finland. I like to see the nature. Give me the plan",
  };
  conversation = await appendMessage(userMsg1, conversation, sessionId);

  const [responseContent, newMessages] = await runAgent(client, conversation);
  console.log(`\nAssistant: ${responseContent}`);

  for (const msg of newMessages) {
    conversation = await appendMessage(msg, conversation, sessionId);
  }

  // Second interaction - check weather
  console.log('\n\n=== Second interaction: Checking weather ===');
  conversation = await appendMessage(
    {
      role: 'user',
      content: 'The plan sounds good, check the weather there',
    },
    conversation,
    sessionId
  );

  const [responseContent2, newMessages2] = await runAgent(
    client,
    conversation
  );
  console.log(`\nAssistant: ${responseContent2}`);

  for (const msg of newMessages2) {
    conversation = await appendMessage(msg, conversation, sessionId);
  }

  // Third interaction - book flight
  console.log('\n\n=== Third interaction: Booking flight ===');
  conversation = await appendMessage(
    {
      role: 'user',
      content:
        'The weather is good, I am in Shanghai now, let\'s book the flight, you should just call the tool and don\'t ask me for more information. Remember, I only want the cheapest flight.',
    },
    conversation,
    sessionId
  );

  const [responseContent3, newMessages3] = await runAgent(
    client,
    conversation
  );
  console.log(`\nAssistant: ${responseContent3}`);

  for (const msg of newMessages3) {
    conversation = await appendMessage(msg, conversation, sessionId);
  }

  await appendMessage(
    {
      role: 'user',
      content: 'cool, everything is done, thank you!',
    },
    conversation,
    sessionId
  );

  console.log(
    `Saved ${conversation.length} messages in conversation, waiting for tasks extraction...`
  );

  // Flush and get tasks
  await acontextClient.sessions.flush(sessionId);
  const tasksResponse = await acontextClient.sessions.getTasks(sessionId);

  console.log('\n=== Extracted Tasks ===');
  for (const task of tasksResponse.items) {
    console.log(`\nTask #${task.order}:`);
    console.log(`  ID: ${task.id}`);
    console.log(`  Title: ${task.data.task_description}`);
    console.log(`  Status: ${task.status}`);

    // Show progress updates if available
    if (task.data.progresses) {
      console.log(`  Progress updates: ${task.data.progresses.length}`);
      for (const progress of task.data.progresses) {
        console.log(`    - ${progress}`);
      }
    }

    // Show user preferences if available
    if (task.data.user_preferences) {
      console.log('  User preferences:');
      for (const pref of task.data.user_preferences) {
        console.log(`    - ${pref}`);
      }
    }
  }
}

async function session2(sessionId: string): Promise<void> {
  const client = createOpenAIClient();

  const messages = await acontextClient.sessions.getMessages(sessionId, {
    format: 'openai',
  });
  const conversation: any[] = messages.items;
  conversation.push({
    role: 'user',
    content: 'Summarize the conversation so far',
  });

  const [responseContent] = await runAgent(client, conversation);
  console.log(`\nAssistant: ${responseContent}`);
}

async function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function main(): Promise<void> {
  const space = await acontextClient.spaces.create();
  const spaceId = space.id;
  console.log(`Created space: ${spaceId}`);

  const session = await acontextClient.sessions.create({ spaceId });
  const sessionId = session.id;
  console.log(`Created session: ${sessionId}`);

  console.log('\n=== Session 1 ===');
  await session1(sessionId);

  console.log('\n=== Session 2, get messages from Acontext and continue ===');
  await session2(sessionId);

  console.log('\n=== Experiences from Acontext ===');
  console.log('Waiting for the agent learning');
  while (true) {
    const status = await acontextClient.sessions.getLearningStatus(sessionId);
    if (status.not_space_digested_count === 0) {
      break;
    }
    await sleep(1000);
    process.stdout.write('.');
  }
  console.log('\n');
  const experienceResult = await acontextClient.spaces.experienceSearch(
    spaceId,
    {
      query: 'travel with flight',
      mode: 'fast',
    }
  );
  console.log(JSON.stringify(experienceResult, null, 2));
}

main().catch(console.error);

