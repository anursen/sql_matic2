// This is a mock service that simulates API calls to a backend
// Later we will replace this with actual API calls

const MOCK_DELAY = 1000; // simulate network delay

const mockResponses = [
  "I can help you with SQL queries. What would you like to know?",
  
  "To create a table in SQL, you can use the `CREATE TABLE` statement. Here's an example:\n\n```sql\nCREATE TABLE employees (\n  employee_id INT PRIMARY KEY,\n  first_name VARCHAR(50),\n  last_name VARCHAR(50),\n  hire_date DATE,\n  salary DECIMAL(10, 2)\n);\n```",
  
  "SELECT statements are used to retrieve data from a database. A basic example:\n\n```sql\nSELECT column1, column2\nFROM table_name\nWHERE condition;\n```",
  
  "You can join tables using different types of joins:\n\n- **INNER JOIN**: Returns records with matching values in both tables\n- **LEFT JOIN**: Returns all records from the left table and matched records from the right\n- **RIGHT JOIN**: Returns all records from the right table and matched records from the left\n- **FULL JOIN**: Returns all records when there's a match in either table",
  
  "SQL aggregation functions include:\n\n| Function | Description |\n|----------|-------------|\n| COUNT() | Counts rows |\n| SUM() | Adds values |\n| AVG() | Calculates average |\n| MIN() | Finds minimum value |\n| MAX() | Finds maximum value |",
  
  "Here's how to filter data with a `WHERE` clause:\n\n```sql\nSELECT *\nFROM customers\nWHERE region = 'North' AND age > 30;\n```",
  
  "You can group data using the `GROUP BY` clause:\n\n```sql\nSELECT department, COUNT(*) as employee_count\nFROM employees\nGROUP BY department;\n```",
  
  "SQL allows you to order results using `ORDER BY`:\n\n```sql\nSELECT product_name, price\nFROM products\nORDER BY price DESC;\n```",
  
  "I'm still learning, but I'm here to help with your SQL questions!"
];

const getRandomResponse = () => {
  const randomIndex = Math.floor(Math.random() * mockResponses.length);
  return mockResponses[randomIndex];
};

const chatService = {
  sendMessage: async (message) => {
    // Simulate API call delay
    await new Promise(resolve => setTimeout(resolve, MOCK_DELAY));
    
    // If message contains SQL keywords, try to provide a relevant response
    let response = getRandomResponse();
    
    if (message.toLowerCase().includes('create table')) {
      response = mockResponses[1];
    } else if (message.toLowerCase().includes('select')) {
      response = mockResponses[2];
    } else if (message.toLowerCase().includes('join')) {
      response = mockResponses[3];
    } else if (message.toLowerCase().includes('count') || message.toLowerCase().includes('sum') || 
              message.toLowerCase().includes('avg') || message.toLowerCase().includes('aggregat')) {
      response = mockResponses[4];
    } else if (message.toLowerCase().includes('where')) {
      response = mockResponses[5];
    } else if (message.toLowerCase().includes('group by')) {
      response = mockResponses[6];
    } else if (message.toLowerCase().includes('order by')) {
      response = mockResponses[7];
    }
    
    // Return response
    return {
      text: response,
      timestamp: new Date().toISOString()
    };
  }
};

export default chatService;
