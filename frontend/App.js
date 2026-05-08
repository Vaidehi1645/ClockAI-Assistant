import React, { useState } from 'react';
import { StyleSheet, Text, View, TextInput, TouchableOpacity, ScrollView, SafeAreaView } from 'react-native';
import axios from 'axios';

// IMPORTANT: Replace with your COMPUTER'S IP ADDRESS (e.g., 192.168.1.5)
// Do not use 'localhost' as the Android emulator/phone won't see it.
const API_URL = "http://192.168.85.197:8000/process";

const workspaces = ['Uni', 'Internship', 'Home'];

export default function App() {
  const [input, setInput] = useState('');
  const [workspace, setWorkspace] = useState('Uni');
  const [messages, setMessages] = useState([
    { role: 'bot', text: "Hello! I'm your AI Clock. Which workspace are we in today?" }
  ]);

  const handleSend = async () => {
  if (!input.trim()) return;
  
  // 1. Add user message to UI immediately
  setMessages(prev => [...prev, { role: 'user', text: input }]);
  setInput('');

  try {
    const response = await axios.post(API_URL, { 
      text: input, 
      workspace: workspace 
    });

    const responseData = response.data;
    const tasks = responseData.tasks || responseData.message || responseData;
    let newMessages = [];

    if (typeof tasks === 'string' && tasks) {
      newMessages.push({ role: 'bot', text: `⚠️ ${tasks}` });
    } else if (Array.isArray(tasks) && tasks.length > 0) {
      tasks.forEach(task => {
        newMessages.push({ 
          role: 'bot', 
          text: `✅ [${workspace}] Scheduled: ${task.data.title} at ${task.data.time}` 
        });
      });
    } else {
      newMessages.push({ role: 'bot', text: "✅ No tasks scheduled." });
    }

    setMessages(prev => [...prev, ...newMessages]);
  } catch (error) {
    console.error(error);
    setMessages(prev => [...prev, { role: 'bot', text: "⚠️ Brain is offline." }]);
  }
};

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>ClockAI Assistant</Text>
      </View>

      <View style={styles.workspaceSelector}>
        {workspaces.map((ws) => (
          <TouchableOpacity
            key={ws}
            style={[styles.workspaceBtn, workspace === ws && styles.workspaceBtnActive]}
            onPress={() => setWorkspace(ws)}
          >
            <Text style={[styles.workspaceBtnText, workspace === ws && styles.workspaceBtnTextActive]}>
              {ws}
            </Text>
          </TouchableOpacity>
        ))}
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
  container: { flex: 1, backgroundColor: '#FAF9F6' },
  header: { padding: 20, backgroundColor: '#FAF9F6', alignItems: 'center', borderBottomWidth: 1, borderBottomColor: '#E0DED8' },
  headerTitle: { color: '#5A5A5A', fontSize: 22, fontWeight: '300', letterSpacing: 3 },
  workspaceSelector: { flexDirection: 'row', justifyContent: 'center', paddingVertical: 12, gap: 10 },
  workspaceBtn: { paddingHorizontal: 20, paddingVertical: 8, borderRadius: 20, backgroundColor: '#E8E6E1' },
  workspaceBtnActive: { backgroundColor: '#8E9775' },
  workspaceBtnText: { color: '#8E9775', fontWeight: '500', fontSize: 14 },
  workspaceBtnTextActive: { color: '#FAF9F6' },
  chatBox: { flex: 1, padding: 15 },
  msgBubble: { padding: 12, borderRadius: 15, marginBottom: 10, maxWidth: '80%' },
  userBubble: { alignSelf: 'flex-end', backgroundColor: '#8E9775' },
  botBubble: { alignSelf: 'flex-start', backgroundColor: '#E8E6E1' },
  msgText: { fontSize: 15, fontWeight: '300', color: '#5A5A5A' },
  inputArea: { flexDirection: 'row', padding: 15, borderTopWidth: 1, borderTopColor: '#E0DED8' },
  input: { flex: 1, backgroundColor: 'white', borderRadius: 20, paddingHorizontal: 15, height: 40, borderWidth: 1, borderColor: '#E0DED8' },
  sendBtn: { marginLeft: 10, justifyContent: 'center', backgroundColor: '#8E9775', borderRadius: 20, paddingHorizontal: 20 },
  sendText: { color: '#FAF9F6', fontWeight: '500' }
});