import React, { useState } from 'react';
import { StyleSheet, Text, View, TextInput, TouchableOpacity, ScrollView, SafeAreaView } from 'react-native';
import axios from 'axios';

// IMPORTANT: Replace with your COMPUTER'S IP ADDRESS (e.g., 192.168.1.5)
// Do not use 'localhost' as the Android emulator/phone won't see it.
const API_URL = "http://192.168.0.89:8000/process";

export default function App() {
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState([
    { role: 'bot', text: "Hello! I'm your AI Clock. Which workspace are we in today?" }
  ]);

  const handleSend = async () => {
    if (!input.trim()) return;

    // Add user message to UI
    const newMessages = [...messages, { role: 'user', text: input }];
    setMessages(newMessages);
    setInput('');

    try {
      const response = await axios.post(API_URL, { text: input });
      const tasks = response.data.tasks;

      // Handle the AI response
      if (tasks && tasks.length > 0) {
        tasks.forEach(task => {
          setMessages(prev => [...prev, { 
            role: 'bot', 
            text: `✅ Scheduled: ${task.data.title} for ${task.data.time}` 
          }]);
        });
      } else {
        setMessages(prev => [...prev, { role: 'bot', text: "Got it, I've updated your schedule." }]);
      }
    } catch (error) {
      console.error(error);
      setMessages(prev => [...prev, { role: 'bot', text: "⚠️ Error connecting to the brain." }]);
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>ClockAI Assistant</Text>
      </View>

      <ScrollView style={styles.chatBox}>
        {messages.map((m, i) => (
          <View key={i} style={[styles.msgBubble, m.role === 'user' ? styles.userBubble : styles.botBubble]}>
            <Text style={styles.msgText}>{m.text}</Text>
          </View>
        ))}
      </ScrollView>

      <View style={styles.inputArea}>
        <TextInput 
          style={styles.input} 
          value={input} 
          onChangeText={setInput} 
          placeholder="e.g., Gym at 7am tomorrow" 
        />
        <TouchableOpacity style={styles.sendBtn} onPress={handleSend}>
          <Text style={styles.sendText}>Send</Text>
        </TouchableOpacity>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f4f7f6' },
  header: { padding: 20, backgroundColor: '#2c3e50', alignItems: 'center' },
  headerTitle: { color: 'white', fontSize: 18, fontWeight: 'bold' },
  chatBox: { flex: 1, padding: 15 },
  msgBubble: { padding: 12, borderRadius: 15, marginBottom: 10, maxWidth: '80%' },
  userBubble: { alignSelf: 'flex-end', backgroundColor: '#3498db' },
  botBubble: { alignSelf: 'flex-start', backgroundColor: '#ecf0f1' },
  msgText: { fontSize: 16 },
  inputArea: { flexDirection: 'row', padding: 15, borderTopWidth: 1, borderColor: '#ddd' },
  input: { flex: 1, backgroundColor: 'white', borderRadius: 20, paddingHorizontal: 15, height: 40 },
  sendBtn: { marginLeft: 10, justifyContent: 'center', backgroundColor: '#2c3e50', borderRadius: 20, paddingHorizontal: 20 },
  sendText: { color: 'white', fontWeight: 'bold' }
});