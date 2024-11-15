import React, { useState } from 'react';
import { View, StyleSheet } from 'react-native';
import { Text, TextInput, Button, IconButton } from 'react-native-paper';
import Icon from 'react-native-vector-icons/MaterialCommunityIcons';
import { ec as EC } from 'elliptic';
const ec = new EC('secp256k1');
import axios from 'axios';


const sendMessage = async (method, ...args) => {
  const payload = {
      jsonrpc: "2.0",
      method: method,
      params: args,
      id: 1,
  };
  try {
      const response = await axios.post('https://rmucxee.localto.net/jsonrpc', payload);
      return response.data;
  } catch (error) {
      console.error('Error sending message:', error);
      return null;
  }
};
const generatePrivateKey = (phrase) => {
  const hash = CryptoJS.SHA256(phrase).toString(CryptoJS.enc.Hex);
  const privateKey = hash.substring(0, 64); // Ensure it's 32 bytes
  return privateKey;
};
const createWallet = (phrase) => {
  const privateKey = generatePrivateKey(phrase);
  const keyPair = ec.keyFromPrivate(privateKey, 'hex');
  const publicKey = keyPair.getPublic().encode('hex');

  const keccakHash = keccak_256(Buffer.from(publicKey, 'hex').slice(1));
  const publicAddress = `0x${keccakHash.slice(-40)}`;

  return { privateKey, publicAddress, publicKey };
};

const Login = () => {
  const [loginType, setLoginType] = useState('donnar');
  const [phrase, setPhrase] = useState('');
  const [uname, setuname] = useState('');

  

  const handleLogin = async() => {
    const { privateKey, publicAddress, publicKey } = createWallet(phrase);
    const result = await sendMessage('create_wallet', {publicAddress,uname});
    setWallet({ privateKey, publicAddress, publicKey });
    wall = publicAddress;
    priv = privateKey;
    console.log(wall);
    if (result.result === "wallet address recived successfully") { 
      navigate('/Home');
       let wall = publicAddress;
    }else if (result.result === "wallet address already added"){
      
      let wall = publicAddress;
      const result = await sendMessage('check_balance', {wall});
      bal= result['result'];
      navigate('/Home');


    }
    else {
      alert('Invalid credentials');
    }
  };

  return (
    <View style={styles.container}>
      <View style={styles.topSection}>
        <View style={styles.iconContainer}>
          <Icon name="account-group" size={30} />
        </View>
        <Text style={styles.title}>CHARITY</Text>
        <Text style={styles.subtitle}>CHAIN</Text>
      </View>

      <View style={styles.buttonGroup}>
        <Button
          mode={loginType === 'charity' ? 'contained' : 'outlined'}
          onPress={() => setLoginType('charity')}
          style={styles.toggleButton}
          buttonColor="#FFD966">
          Charity Login
        </Button>
        <Button
          mode={loginType === 'donnar' ? 'contained' : 'outlined'}
          onPress={() => setLoginType('donnar')}
          style={styles.toggleButton}
          buttonColor="#FFD966">
          Donnar's Login
        </Button>
      </View>

      <View style={styles.formContainer}>
        <Text style={styles.formTitle}>
          {loginType === 'charity' ? 'Charity Login' : "User's Login"}
        </Text>

        <TextInput
          left={<TextInput.Icon icon="email" />}
          mode="outlined"
          placeholder="Name"
          value={uname}
          onChangeText={setuname}
          style={styles.input}
        />

        <TextInput
          left={<TextInput.Icon icon="lock" />}
          mode="outlined"
          secureTextEntry
          placeholder="Phrase"
          value={phrase}
          onChangeText={setPhrase}
          style={styles.input}
        />


        <Button
          mode="contained"
          onPress={handleLogin}
          style={styles.loginButton}
          buttonColor="#000">
          Login
        </Button>

        <View style={styles.socialButtons}>
          <IconButton icon="google" size={24} />
          <IconButton icon="facebook" size={24} />
        </View>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: 'white',
  },
  topSection: {
    height: 250,
    backgroundColor: '#FFD966',
    borderBottomLeftRadius: 100,
    borderBottomRightRadius: 100,
    alignItems: 'center',
    justifyContent: 'center',
  },
  iconContainer: {
    backgroundColor: '#FFF5D6',
    padding: 16,
    borderRadius: 50,
    marginBottom: 16,
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
  },
  subtitle: {
    color: '#666',
  },
  buttonGroup: {
    flexDirection: 'row',
    justifyContent: 'center',
    gap: 16,
    marginTop: 24,
    paddingHorizontal: 16,
  },
  toggleButton: {
    borderRadius: 25,
  },
  formContainer: {
    padding: 16,
    gap: 16,
  },
  formTitle: {
    fontSize: 18,
    fontWeight: '600',
    marginBottom: 16,
  },
  input: {
    marginBottom: 16,
  },
  forgotPassword: {
    textAlign: 'right',
    color: '#666',
  },
  loginButton: {
    marginTop: 16,
    borderRadius: 8,
  },
  socialButtons: {
    flexDirection: 'row',
    justifyContent: 'center',
    marginTop: 16,
  },
});

export default Login;