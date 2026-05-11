import React, { useState } from 'react';
import { StyleSheet, Text, View, TextInput, TouchableOpacity, ScrollView, SafeAreaView, Alert, Platform, Linking, KeyboardAvoidingView, Platform as RNPlatform } from 'react-native';
import axios from 'axios';

const API_URL = "http://192.168.85.22:8000/process";

const setAndroidAlarm = (time, title) => {
  if (Platform.OS !== 'android') return;
  
  const [hours, minutes] = time.split(':').map(Number);
  
  try {
    const androidPkg = "com.android.deskclock";
    const intentUrl = `intent://alarmclock?hour=${hours}&minutes=${minutes}&message=${encodeURIComponent(title)}&show_actions=true#Intent;package=${androidPkg}`;
    
    Linking.openURL(intentUrl).catch(() => {
      Alert.alert("Manual Set", `Open Clock app and set ${title} at ${time}`);
    });
  } catch (e) {
    Alert.alert("Note", `Schedule saved. Set alarm manually for ${time}`);
  }
};

const initialMessages = {
  'Uni': [{ role: 'bot', text: "Hello! I'm ClockAI. You're in Uni workspace. What would you like to schedule?" }],
  'Internship': [{ role: 'bot', text: "Hello! I'm ClockAI. You're in Internship workspace. What would you like to schedule?" }],
  'Home': [{ role: 'bot', text: "Hello! I'm ClockAI. You're in Home workspace. What would you like to schedule?" }]
};

export default function App() {
  const [input, setInput] = useState('');
  const [workspace, setWorkspace] = useState('Uni');
  const [messages, setMessages] = useState(initialMessages);
  const [workspaces, setWorkspaces] = useState(['Uni', 'Internship', 'Home']);
  const [showAddWorkspace, setShowAddWorkspace] = useState(false);
  const [newWorkspaceName, setNewWorkspaceName] = useState('');
  const [toast, setToast] = useState(null);

  const showToast = (message) => {
    setToast(message);
    setTimeout(() => setToast(null), 2000);
  };

  const currentMessages = messages[workspace];

  const resetChat = () => {
    setMessages(prev => ({
      ...prev,
      [workspace]: [{ role: 'bot', text: "New chat started. How can I help you schedule today?" }]
    }));
  };

  const handleWorkspaceChange = (newWorkspace) => {
    if (newWorkspace !== workspace) {
      if (!messages[newWorkspace] || messages[newWorkspace].length === 0) {
        setMessages(prev => ({
          ...prev,
          [newWorkspace]: [{ role: 'bot', text: `Switched to ${newWorkspace} workspace. What would you like to schedule?` }]
        }));
      }
      setWorkspace(newWorkspace);
      setInput('');
    }
  };

  const handleAddWorkspace = () => {
    const trimmedName = newWorkspaceName.trim();
    if (!trimmedName) {
      setShowAddWorkspace(false);
      setNewWorkspaceName('');
      return;
    }
    if (workspaces.includes(trimmedName)) {
      setNewWorkspaceName('');
      setShowAddWorkspace(false);
      return;
    }
    setWorkspaces(prev => [...prev, trimmedName]);
    setMessages(prev => ({
      ...prev,
      [trimmedName]: [{ role: 'bot', text: `Switched to ${trimmedName} workspace. What would you like to schedule?` }]
    }));
    setWorkspace(trimmedName);
    setNewWorkspaceName('');
    setShowAddWorkspace(false);
  };

  const handleDeleteWorkspace = (wsName) => {
    Alert.alert(
      'Delete Workspace',
      `Are you sure you want to delete "${wsName}"?`,
      [
        { text: 'Cancel', style: 'cancel' },
        { 
          text: 'Delete', 
          style: 'destructive',
          onPress: () => {
            const remainingWorkspaces = workspaces.filter(w => w !== wsName);
            setWorkspaces(remainingWorkspaces);
            setMessages(prev => {
              const newMessages = { ...prev };
              delete newMessages[wsName];
              return newMessages;
            });
            if (workspace === wsName) {
              setWorkspace(remainingWorkspaces[0] || 'Uni');
            }
            showToast(`"${wsName}" deleted successfully`);
          }
        }
      ]
    );
  };

  const handleSend = async () => {
    if (!input.trim()) return;
    
    if (input.includes('image://') || input.includes('photos')) {
      setMessages(prev => ({
        ...prev,
        [workspace]: [...prev[workspace], { role: 'bot', text: "I can only process text. Please type your schedule request." }]
      }));
      return;
    }
    
    setMessages(prev => ({
      ...prev,
      [workspace]: [...prev[workspace], { role: 'user', text: input }]
    }));
    setInput('');

    try {
      const response = await axios.post(API_URL, { 
        text: input, 
        workspace: workspace 
      });

      const data = response.data;
      let newMessages = [];

      if (data.type === 'greeting') {
        newMessages.push({ role: 'bot', text: data.message });
      } 
      else if (data.type === 'conflict') {
        data.conflicts.forEach((conflict, idx) => {
          newMessages.push({ 
            role: 'bot', 
            text: `⚠️ ${conflict.message}`,
            isConflict: true,
            pendingTask: conflict.task,
            conflictIndex: idx
          });
        });
      }
      else if (data.type === 'success' && data.tasks) {
        data.tasks.forEach(task => {
          const title = task.data?.title || 'Untitled';
          const time = task.data?.time || 'unknown time';
          newMessages.push({ 
            role: 'bot', 
            text: `✅ [${workspace}] Scheduled: ${title} at ${time}` 
          });
          
          if (task.data?.time) {
            setAndroidAlarm(task.data.time, title);
          }
        });
      }
      else if (data.type === 'no_tasks') {
        newMessages.push({ role: 'bot', text: data.message || "✅ No tasks scheduled." });
      }
      else if (data.type === 'error') {
        newMessages.push({ role: 'bot', text: `⚠️ ${data.message || 'Something went wrong. Please try again.'}` });
      }

      setMessages(prev => ({
        ...prev,
        [workspace]: [...prev[workspace], ...newMessages]
      }));
    } catch (error) {
      setMessages(prev => ({
        ...prev,
        [workspace]: [...prev[workspace], { role: 'bot', text: "⚠️ Brain is offline." }]
      }));
    }
  };

  const handleOverride = async (task, ws) => {
    const taskData = task.data || task;
    const overrideText = `Schedule ${taskData.title} at ${taskData.time} - HIGH PRIORITY - override existing`;
    
    try {
      const response = await axios.post(API_URL, { 
        text: overrideText, 
        workspace: ws 
      });
      
      const data = response.data;
      setMessages(prev => {
        const filtered = prev[ws].filter(m => m.pendingTask !== task);
        return { 
          ...prev, 
          [ws]: [...filtered, { role: 'bot', text: `✅ Overwritten! ${taskData.title} at ${taskData.time}` }] 
        };
      });
      
    } catch (error) {
      setMessages(prev => ({
        ...prev,
        [ws]: [...prev[ws], { role: 'bot', text: "⚠️ Something went wrong." }]
      }));
    }
  };

  const handleScheduleAnyway = async (task, ws) => {
    const taskData = task.data || task;
    const anywayText = `Schedule ${taskData.title} at ${taskData.time} anyway`;
    
    try {
      const response = await axios.post(API_URL, { 
        text: anywayText, 
        workspace: ws 
      });
      
      const data = response.data;
      setMessages(prev => {
        const filtered = prev[ws].filter(m => m.pendingTask !== task);
        return { 
          ...prev, 
          [ws]: [...filtered, { role: 'bot', text: `✅ Scheduled! ${taskData.title} at ${taskData.time}` }] 
        };
      });
      
    } catch (error) {
      setMessages(prev => ({
        ...prev,
        [ws]: [...prev[ws], { role: 'bot', text: "⚠️ Something went wrong." }]
      }));
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      <KeyboardAvoidingView 
        behavior={RNPlatform.OS === 'ios' ? 'padding' : 'height'}
        style={styles.keyboardView}
        keyboardVerticalOffset={0}
      >
        <View style={styles.header}>
          <TouchableOpacity onPress={resetChat} style={styles.newChatBtn}>
            <Text style={styles.newChatText}>+ New Chat</Text>
          </TouchableOpacity>
          <Text style={styles.headerTitle}>ClockAI</Text>
          <View style={{width: 60}} />
        </View>

        <View style={styles.workspaceSelector}>
          <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.workspaceScrollContent}>
            {workspaces.map((ws) => (
              <TouchableOpacity
                key={ws}
                style={[styles.workspaceBtn, workspace === ws && styles.workspaceBtnActive]}
                onPress={() => handleWorkspaceChange(ws)}
                onLongPress={() => handleDeleteWorkspace(ws)}
              >
                <Text style={[styles.workspaceBtnText, workspace === ws && styles.workspaceBtnTextActive]}>
                  {ws}
                </Text>
              </TouchableOpacity>
            ))}
            <TouchableOpacity style={styles.addWorkspaceBtn} onPress={() => setShowAddWorkspace(true)}>
              <Text style={styles.addWorkspaceBtnText}>+</Text>
            </TouchableOpacity>
          </ScrollView>
        </View>

        <ScrollView style={styles.chatBox} keyboardShouldPersistTaps="handled">
          {currentMessages.map((m, i) => (
            <View key={i} style={[
              styles.msgBubble, 
              m.role === 'user' ? styles.userBubble : 
              m.isConflict ? styles.conflictBubble : styles.botBubble
            ]}>
              <Text style={styles.msgText}>{m.text}</Text>
              {m.isConflict && m.pendingTask && (
                <View style={styles.conflictButtons}>
                  <TouchableOpacity 
                    style={[styles.conflictBtn, {backgroundColor: '#8E9775'}]}
                    onPress={() => handleOverride(m.pendingTask, workspace)}
                  >
                    <Text style={styles.conflictBtnText}>Override</Text>
                  </TouchableOpacity>
                  <TouchableOpacity 
                    style={[styles.conflictBtn, {backgroundColor: '#A0A0A0'}]}
                    onPress={() => handleScheduleAnyway(m.pendingTask, workspace)}
                  >
                    <Text style={styles.conflictBtnText}>Schedule Anyway</Text>
                  </TouchableOpacity>
                </View>
              )}
            </View>
          ))}
        </ScrollView>

        <View style={styles.inputArea}>
          <TextInput 
            style={styles.input} 
            value={input} 
            onChangeText={setInput} 
            placeholder={`Message ${workspace}...`}
            placeholderTextColor="#999"
          />
          <TouchableOpacity style={styles.sendBtn} onPress={handleSend}>
            <Text style={styles.sendText}>Send</Text>
          </TouchableOpacity>
        </View>
      </KeyboardAvoidingView>

      {showAddWorkspace && (
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <Text style={styles.modalTitle}>New Workspace</Text>
            <TextInput
              style={styles.modalInput}
              placeholder="Enter workspace name"
              placeholderTextColor="#999"
              value={newWorkspaceName}
              onChangeText={setNewWorkspaceName}
              autoFocus
            />
            <View style={styles.modalButtons}>
              <TouchableOpacity style={styles.modalCancelBtn} onPress={() => { setShowAddWorkspace(false); setNewWorkspaceName(''); }}>
                <Text style={styles.modalCancelText}>Cancel</Text>
              </TouchableOpacity>
              <TouchableOpacity style={styles.modalCreateBtn} onPress={handleAddWorkspace}>
                <Text style={styles.modalCreateText}>Create</Text>
              </TouchableOpacity>
            </View>
          </View>
        </View>
      )}

      {toast && (
        <View style={styles.toast}>
          <Text style={styles.toastText}>{toast}</Text>
        </View>
      )}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#FAF9F6' },
  keyboardView: { flex: 1 },
  header: { padding: 15, paddingTop: 10, backgroundColor: '#FAF9F6', alignItems: 'center', borderBottomWidth: 1, borderBottomColor: '#E0DED8', flexDirection: 'row', justifyContent: 'space-between' },
  headerTitle: { color: '#5A5A5A', fontSize: 22, fontWeight: '300', letterSpacing: 3 },
  newChatBtn: { backgroundColor: '#8E9775', paddingHorizontal: 12, paddingVertical: 6, borderRadius: 15 },
  newChatText: { color: '#FAF9F6', fontSize: 12, fontWeight: '600' },
  workspaceSelector: { paddingVertical: 12 },
  workspaceScrollContent: { justifyContent: 'center', gap: 10, paddingHorizontal: 15 },
  workspaceBtn: { paddingHorizontal: 20, paddingVertical: 8, borderRadius: 20, backgroundColor: '#E8E6E1' },
  workspaceBtnActive: { backgroundColor: '#8E9775' },
  workspaceBtnText: { color: '#8E9775', fontWeight: '500', fontSize: 14 },
  workspaceBtnTextActive: { color: '#FAF9F6' },
  addWorkspaceBtn: { paddingHorizontal: 14, paddingVertical: 8, borderRadius: 20, backgroundColor: '#D4D2CD', alignItems: 'center', justifyContent: 'center' },
  addWorkspaceBtnText: { color: '#8E9775', fontWeight: '600', fontSize: 16, lineHeight: 18 },
  chatBox: { flex: 1, padding: 15 },
  msgBubble: { padding: 12, borderRadius: 15, marginBottom: 10, maxWidth: '80%' },
  userBubble: { alignSelf: 'flex-end', backgroundColor: '#8E9775' },
  botBubble: { alignSelf: 'flex-start', backgroundColor: '#E8E6E1' },
  conflictBubble: { alignSelf: 'flex-start', backgroundColor: '#FFE4B5', borderWidth: 1, borderColor: '#DAA520' },
  conflictButtons: { flexDirection: 'row', marginTop: 10, gap: 8 },
  conflictBtn: { paddingHorizontal: 12, paddingVertical: 6, borderRadius: 15 },
  conflictBtnText: { color: 'white', fontSize: 12, fontWeight: '500' },
  msgText: { fontSize: 15, fontWeight: '300', color: '#5A5A5A' },
  inputArea: { flexDirection: 'row', padding: 15, borderTopWidth: 1, borderTopColor: '#E0DED8' },
  input: { flex: 1, backgroundColor: 'white', borderRadius: 20, paddingHorizontal: 15, height: 40, borderWidth: 1, borderColor: '#E0DED8', color: '#5A5A5A' },
  sendBtn: { marginLeft: 10, justifyContent: 'center', backgroundColor: '#8E9775', borderRadius: 20, paddingHorizontal: 20 },
  sendText: { color: '#FAF9F6', fontWeight: '500' },
  modalOverlay: { position: 'absolute', top: 0, left: 0, right: 0, bottom: 0, backgroundColor: 'rgba(0,0,0,0.5)', justifyContent: 'center', alignItems: 'center' },
  modalContent: { backgroundColor: '#FAF9F6', borderRadius: 15, padding: 20, width: '80%', maxWidth: 300 },
  modalTitle: { fontSize: 18, fontWeight: '600', color: '#5A5A5A', marginBottom: 15, textAlign: 'center' },
  modalInput: { backgroundColor: 'white', borderRadius: 10, paddingHorizontal: 15, paddingVertical: 12, borderWidth: 1, borderColor: '#E0DED8', color: '#5A5A5A', marginBottom: 15 },
  modalButtons: { flexDirection: 'row', justifyContent: 'space-between', gap: 10 },
  modalCancelBtn: { flex: 1, paddingVertical: 12, borderRadius: 10, backgroundColor: '#E8E6E1', alignItems: 'center' },
  modalCancelText: { color: '#5A5A5A', fontWeight: '500' },
  modalCreateBtn: { flex: 1, paddingVertical: 12, borderRadius: 10, backgroundColor: '#8E9775', alignItems: 'center' },
  modalCreateText: { color: '#FAF9F6', fontWeight: '600' },
  toast: { position: 'absolute', bottom: 100, left: 20, right: 20, backgroundColor: '#5A5A5A', borderRadius: 10, paddingVertical: 12, paddingHorizontal: 20, alignItems: 'center' },
  toastText: { color: '#FAF9F6', fontSize: 14, fontWeight: '500' }
});