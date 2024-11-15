import React, { useState , useEffect,useCallback} from 'react';
import { View, Text, StyleSheet, FlatList, TouchableOpacity, TextInput,Modal ,Platform, ScrollView} from 'react-native';
import * as DocumentPicker from 'expo-document-picker';
import { NavigationContainer } from '@react-navigation/native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { createStackNavigator } from '@react-navigation/stack';
import { Ionicons, MaterialCommunityIcons } from '@expo/vector-icons';
import axios from 'axios';
import * as FileSystem from 'expo-file-system';
import { BarCodeScanner } from 'expo-barcode-scanner';
import QRCode from 'react-native-qrcode-svg';
import CryptoJS from 'crypto-js';
import { ec as EC } from 'elliptic';
const ec = new EC('secp256k1');
import { keccak_256 } from 'js-sha3';
import { Buffer } from 'buffer';
import { LinearGradient } from 'expo-linear-gradient';
import * as MediaLibrary from 'expo-media-library';
import { useFocusEffect } from '@react-navigation/native';
import { useIsFocused } from '@react-navigation/native';
import { StorageAccessFramework } from 'expo-file-system';
import login from './screens/login.js';
import loginn from './screens/login.js';
var wall= null;
var priv = null;
var sdata = null;
var bal = null;

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

function createTransactionHash(transaction) {
  console.log("to address:")
  console.log(transaction.to);
  const toAddress = transaction.to.toLowerCase().replace('0x', '');

  if (toAddress.length !== 40 || !/^[0-9a-f]+$/.test(toAddress)) {
      throw new Error("Invalid 'to' address format");
  }
  const toBytes = Buffer.from(toAddress, 'hex');
  const nonce = Buffer.alloc(32);
  nonce.writeBigUInt64BE(BigInt(transaction.nonce), 24);
  const gasPrice = Buffer.alloc(32);
  gasPrice.writeBigUInt64BE(BigInt(transaction.gasPrice), 24);
  const gasLimit = Buffer.alloc(32);
  gasLimit.writeBigUInt64BE(BigInt(transaction.gasLimit), 24);
  const value = Buffer.alloc(32);
  value.writeBigUInt64BE(BigInt(transaction.value), 24);
  const data = Buffer.from(transaction.data, 'utf-8');
  const hashBuffer = Buffer.concat([nonce, gasPrice, gasLimit, toBytes, value, data]);
  const testHash = keccak_256(hashBuffer);
  return Buffer.from(testHash, 'hex');
}


function signTransaction(transaction, privateKey) {
  const txHash = createTransactionHash(transaction);
  const keyPair = ec.keyFromPrivate(privateKey, 'hex');
  const signature = keyPair.sign(txHash, { canonical: true });

  const r = signature.r.toString(10); 
  const s = signature.s.toString(10); 
  const v = 27 + signature.recoveryParam; 

  return { v, r: r, s: s };
}

const handleRecoverPublicKey = (transaction, v, r, s) => {
  const txHash = createTransactionHash(transaction);
  const signature = { r: BigInt(r).toString(16), s: BigInt(s).toString(16) };
  console.log(signature)
  const recoveryParam = v - 27;
  
  const key = ec.recoverPubKey(txHash, signature, recoveryParam);
  const publicKey = ec.keyFromPublic(key).getPublic().encode('hex', false);

  const publicKeyBuffer = Buffer.from(publicKey, 'hex');
  const publicKeyHash = keccak_256(publicKeyBuffer.slice(1)); 
  const recoveredAddress = '0x' + publicKeyHash.slice(-40); 

  if (recoveredAddress.toLowerCase() === transaction.from) {
      console.log('The recovered sender address matches the original sender address.');
      Alert.alert('Sucessfully verified', `Actual senders Address: ${recoveredAddress.toLowerCase()}\n\n  Recovered address: ${transaction.from}`);
  } else {
      console.error('The recovered sender address does not match the original sender address.');
  }
};

const LoginScreen = ({ navigation }) => {
  const [wallet, setWallet] = useState(null);
  const [phrase, setPhrase] = useState('');
  const [pname, setpname] = useState('');
  const [uname, setuname] = useState('');

  

  const handleLogin = async() => {
    const { privateKey, publicAddress, publicKey } = createWallet(phrase);
    const result = await sendMessage('create_wallet', {publicAddress,uname});
    setWallet({ privateKey, publicAddress, publicKey });
    wall = publicAddress;
    priv = privateKey;
    console.log(wall);
    if (result.result === "wallet address recived successfully") { 
      navigation.replace('Main');
       let wall = publicAddress;
    }else if (result.result === "wallet address already added"){
      
      let wall = publicAddress;
      const result = await sendMessage('check_balance', {wall});
      bal= result['result'];
      navigation.replace('Main');

    }
    else {
      alert('Invalid credentials');
    }
  };

  const handleprojectcreation = async() => {
    const { privateKey, publicAddress, publicKey } = createWallet(pname);
    const result = await sendMessage('create_project', {publicAddress,pname});
    setWallet({ privateKey, publicAddress, publicKey });
    wall = publicAddress;
    priv = privateKey;
    console.log(wall);
    if (result.result === "wallet address recived successfully") { 
      navigation.replace('Main');
       let wall = publicAddress;
    }else if (result.result === "wallet address already added"){
      
      let wall = publicAddress;
      const result = await sendMessage('check_balance', {wall});
      bal= result['result'];
      navigation.replace('Main');

    }
    else {
      alert('Invalid credentials');
    }
  };

  return (

    <View style={styles.loginContainer}>
    <View style={{width:"100%",height:"12%",backgroundColor:"white",alignContent:'stretch',alignItems:'center',shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 5,}}>
    <Text style={{color:'black',fontSize:30,}}> Charity Chain</Text>  
    </View>
      
      <Text style={styles.loginLabel}>Enter Name :</Text>
      <TextInput
        style={styles.input1}
        placeholder="Name"
        value={uname}
        onChangeText={setuname}
      />
      <Text style={styles.loginLabel}>Enter Phrase :</Text>
      <TextInput
        style={styles.input1}
        placeholder="Phrase"
        value={phrase}
        onChangeText={setPhrase}
      />
      <TouchableOpacity onPress={handleLogin} style={styles.buttonContainer1}>
        <LinearGradient
          colors={['#000000', '#000000']}
          style={styles.button1}
        >
          <Text style={styles.buttonText1}>Login</Text>
        </LinearGradient>
      </TouchableOpacity>

      <Text style={styles.loginLabel}>Enter Project Name :</Text>
      <TextInput
        style={styles.input1}
        placeholder="Project name"
        value={pname}
        onChangeText={setpname}
      />
      <TouchableOpacity onPress={handleprojectcreation} style={styles.buttonContainer1}>
        <LinearGradient
          colors={['#000000', '#000000']}
          style={styles.button1}
        >
          <Text style={styles.buttonText1}>Create Project</Text>
        </LinearGradient>
      </TouchableOpacity>

    </View>

  );
};


const ReciScreen = () => {

  const [inputText, setInputText] = useState('');

  return (
    <View style={styles.container}>
    <View style={{marginBottom:0,borderWidth:1,width:"100%",height:90,backgroundColor:"black",marginTop:40}}>
    <Text style={{color:'white',marginTop:20,fontSize:30,marginLeft:135}}> Charity Chain</Text>
    </View>
      <View style={styles.qrContainer}>

        <QRCode value={inputText || wall} size={200} />
      </View>
    </View>
  );
};



const Settings = ({ navigation }) => {


  const handlelogout= async() => {
 
    navigation.navigate("Login");
  };
  const handletest= async() => {
 
    navigation.navigate("login");
  };
  return (
    <View style={styles.container1}>
        <View style={{marginBottom: 0,borderWidth:1,width:"100%",height:90,backgroundColor:"black",marginTop:40}}>
    <Text style={{color:'white',marginTop:20,fontSize:30,marginLeft:135}}> Charity Chain</Text>  
    </View>
    <Text style={{color:'black',marginTop:20,fontSize:30, marginRight:10,marginBottom:20,alignSelf:'center'}}> Settings</Text>  
      <TouchableOpacity  style={styles.buttonContainer1} on onPress={handletest}>
        <LinearGradient
          colors={['#000000', '#000000']}
          style={styles.button1}
        >
          <Text style={styles.buttonText1}>Button </Text>
        </LinearGradient>
      </TouchableOpacity>


      <TouchableOpacity onPress={handlelogout} style={{width: '80%',borderRadius: 10,margin:10}}>
        <LinearGradient
          colors={['#000000', '#000000']}
          style={{height: 50,justifyContent: 'center',alignItems: 'center',borderRadius: 10,}}>
          <Text style={styles.buttonText1}>Logout</Text>
        </LinearGradient>
      </TouchableOpacity>
    </View>
  );
};


const Sendto = ({ navigation }) => {
  const [amount, setAmount] = useState('');
  const [walletAddress, setwalletaddress] = useState('');

  const handleSend = async() => {
    var transaction = {
      nonce: 0,
      gasPrice: 20000000000,
      gasLimit: 21000,
      to: String(walletAddress),
      value: parseInt(amount),
      data: '',
      from: String(wall)
  };
  const signature = signTransaction(transaction, priv);
  const result = await sendMessage('transaction_android', [transaction, signature.v, signature.r, signature.s]);
  console.log(result);
    setAmount('');
    navigation.navigate('Home');
    alert(`Sending ${amount} to ${sdata}`);

  };

  return (
    <View style={styles.container1}>
    <View style={{marginBottom: 180,borderWidth:1,width:"100%",height:90,backgroundColor:"black",marginTop:40}}>
    <Text style={{color:'white',marginTop:20,fontSize:30,marginLeft:135}}>Charity Chain</Text>  

    </View>
      <Text style={styles.label1}>Wallet Address:</Text>
      <TextInput
        style={styles.input1}
        value={walletAddress}
        onChangeText={setwalletaddress}
      />
      <Text style={styles.label1}>Amount:</Text>
       <TextInput
        style={styles.input1}
        value={amount}
        onChangeText={setAmount}
        keyboardType="numeric"
      />
      <TouchableOpacity onPress={handleSend} style={styles.buttonContainer1}>
        <LinearGradient
          colors={['#000000', '#000000']}
          style={styles.button1}
        >
          <Text style={styles.buttonText1}>SEND</Text>
        </LinearGradient>
      </TouchableOpacity>
    </View>
  );
};



const SScreen = ({ navigation }) => {
  const [amount, setAmount] = useState('');
  const walletAddress = '';
  console.log(sdata);

  const handleSend = async() => {
    var transaction = {
      nonce: 0,
      gasPrice: 20000000000,
      gasLimit: 21000,
      to: String(sdata),
      value: parseInt(amount),
      data: '',
      from: String(wall)
  };
  const signature = signTransaction(transaction, priv);
  const result = await sendMessage('transaction_android', [transaction, signature.v, signature.r, signature.s]);
  console.log(result);
    setAmount('');
    navigation.navigate('Home');
    alert(`Sending ${amount} to ${sdata}`);

  };

  return (
    <View style={styles.container1}>
        <View style={{marginBottom: 230,borderWidth:1,width:"100%",height:90,backgroundColor:"black",marginTop:40}}>
    <Text style={{color:'white',marginTop:20,fontSize:30,marginLeft:135}}> Charity Chain</Text>  
    </View>
      <Text style={styles.label1}>Wallet Address:</Text>
      <Text style={styles.address1}>{sdata}</Text>
      <TextInput
        style={styles.input1}
        value={amount}
        onChangeText={setAmount}
        keyboardType="numeric"
      />
      <TouchableOpacity onPress={handleSend} style={styles.buttonContainer1}>
        <LinearGradient
          colors={['#000000', '#000000']}
          style={styles.button1}
        >
          <Text style={styles.buttonText1}>SEND</Text>
        </LinearGradient>
      </TouchableOpacity>
    </View>
  );
}; 


const ScanScreen = ({ navigation }) => {
  const [hasPermission, setHasPermission] = useState(null);
  const [scanned, setScanned] = useState(false);
  const isFocused = useIsFocused();
  useEffect(() => {
    (async () => {
      const { status } = await BarCodeScanner.requestPermissionsAsync();
      setHasPermission(status === 'granted');
    })();
  }, []);

  useFocusEffect(
    
    useCallback(() => {
      console.log('check');
      setScanned(false);
      
    }, [])
    
  );

  const handleBarCodeScanned = ({ type, data }) => {
    if (!scanned) {
      setScanned(true);
      console.log(data);
      sdata = data;
      navigation.navigate('ss');
    }
  };

  if (hasPermission === null) {
    return <Text>Requesting for camera permission</Text>;
  }
  if (hasPermission === false) {
    return <Text>No access to camera</Text>;
  }

  return (
    <View style={styles.container1}>
        <View style={{marginBottom:0,borderWidth:1,width:"100%",height:90,backgroundColor:"black",marginTop:40}}>
    <Text style={{color:'white',marginTop:20,fontSize:30,marginLeft:135}}> Charity Chain</Text>  
    </View>
    <Text style={{color:"black",marginTop:30,fontSize:30,justifyContent:'center'}}> Scan To Send </Text>
      <View style={styles.scannerContainer}>
      {isFocused ? (
        <BarCodeScanner
          onBarCodeScanned={scanned ? undefined : handleBarCodeScanned}
          style={[StyleSheet.absoluteFill, styles.cam]}
        />
      ) : null}
      </View>
    </View>
  );
};


const HomeScreen = () => {
  const [to_address, setto] = useState('');
  const [files, setFiles] = useState([
  ]);

  const chk_bal = async () => {
          let files;
          files = await sendMessage('check_files', {wall});
          console.log(files)
          if (files['result'] === "No files Uploaded")
            {setFiles();}
          else{setFiles(files['result']);}
    }

    useFocusEffect(
    
      useCallback(() => {
        let subcription;
        let files;
        const getbalance = async() => {
          subcription = await sendMessage('check_balance', {wall});
          balance = String(subcription['result']);
          setto(balance);
          files = await sendMessage('check_files', {wall});
          console.log(files)
          if (files['result'] === "No files Uploaded")
            {setFiles();}
          else{setFiles(files['result']);}

        }
        getbalance();
        return () => {  }
      }, [])
      
    );

  const pickFile = async () => {
    try {
      const r1 = await DocumentPicker.getDocumentAsync({
        type: '*/*', 
      });
      const r2 = r1['assets'];
      var result = r2[0]
      var fname = result.name;  
      var size = result.size;
      if (result.uri) {

        convertToBase64(result.uri,fname,size);
        
      }
    } catch (error) {
      console.error('Error picking file: ', error);
    }
  };
  
  const getMimeType = (fileName) => {
    const extension = fileName.split('.').pop().toLowerCase();
    switch (extension) {
      case 'jpg':
      case 'jpeg':
        return 'image/jpeg';
      case 'png':
        return 'image/png';
      case 'pdf':
        return 'application/pdf';
      case 'doc':
      case 'docx':
        return 'application/msword';
      case 'xls':
      case 'xlsx':
        return 'application/vnd.ms-excel';
      case 'txt':
        return 'text/plain';
      default:
        return 'application/octet-stream'; // Default MIME type
    }
  };
  

  const convertToBase64 = async (r1,fname,fsize) => {
    console.log(r1);
    try {
      if (!r1) return;
      const base64 = await FileSystem.readAsStringAsync(r1, {
        encoding: FileSystem.EncodingType.Base64,
      });
      const payload = { name: fname, size: String(fsize), base64 ,wall};
      console.log('Base64: ', base64);
      const result = await sendMessage("receive_file", payload);
      console.log(result);
    } catch (error) {
      console.error('Error converting file to base64: ', error);
    }
  };

  const [isModalVisible, setModalVisible] = useState(false);
  const [selectedItem, setSelectedItem] = useState(null);

  const handleItemPress = (item) => {

    setSelectedItem(item);

    setModalVisible(true);
  };

  const handleModalButtonPress = async () => {
    const payload = { name: selectedItem['name'], wall };
    const result = await sendMessage("get_file_base64", payload);
    console.log(result);
    const base64String = result['result'];
    const permissions = await StorageAccessFramework.requestDirectoryPermissionsAsync();
    if (!permissions.granted) {
      return;
  }
    try {
      if (!base64String) return;

      // Request permission to write to the media library
      const { status } = await MediaLibrary.requestPermissionsAsync();
      if (status !== 'granted') {
        alert('Permission to access media library is required!');
        return;
      }
      const mimeType = getMimeType(selectedItem['name']);
      // Use the cache directory to save the file initially
      try {
        await StorageAccessFramework.createFileAsync(permissions.directoryUri, selectedItem['name'], mimeType)
            .then(async(uri) => {
                await FileSystem.writeAsStringAsync(uri, base64String, { encoding: FileSystem.EncodingType.Base64 });
            })
            .catch((e) => {
                console.log(e);
            });
    } catch (e) {
        throw new Error(e);
    }
    } catch (error) {
      console.error('Error converting base64 to file: ', error);
    }

    console.log('Button pressed inside modal with item:', selectedItem);
    setModalVisible(false);
  };



  const handleModalButtondelete = async() => {
    const payload = { name: selectedItem['name'] ,wall};
    const result = await sendMessage("delete_files", payload);
    console.log('Button pressed inside modal with item:', selectedItem['name']);
    setModalVisible(false); 
  };

  const renderItem = ({ item }) => (
    <View style={styles.fileContainer}>
      <TouchableOpacity onPress={() => handleItemPress(item)}>

    <Ionicons name="folder-open-outline" size={24} color="black" />
      <Text style={styles.fileName}>{item.name}</Text>
      </TouchableOpacity>
    </View>
  );

  return (
    <View style={styles.container}>
        <View style={{marginBottom: 0,borderWidth:1,width:"100%",height:90,backgroundColor:"black",marginTop:40}}>
    <Text style={{color:'white',marginTop:20,fontSize:30,marginLeft:135}}> Charity Chain</Text>  
    </View>
    <View style={{borderWidth:1,borderRadius:10,borderBlockColor:"#AEAEAE",margin:15,shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.1,
    shadowRadius: 8,}}>
      <Text style={styles.walletLabel}>WALLET ADDRESS :</Text>
      <Text style={styles.walletAddress}>{wall}</Text>
      </View>
      <View style={styles.balance1}>
      <Text style={{fontSize: 24,fontWeight: 'bold',marginLeft:10,marginTop:3,color:'black',}}>{to_address}</Text>
      </View>
      <TouchableOpacity style={{borderWidth:1,height:"5%",marginTop:15,marginLeft:15,marginRight:15,
      borderRadius:10,borderBlockColor:"#AEAEAE" ,backgroundColor:'black',justifyContent:'center',} }onPress={chk_bal}>
      <Text style={styles.buttonText3}>REFRESH</Text>

      </TouchableOpacity>
      <FlatList
        data={files}
        renderItem={renderItem}
        keyExtractor={(item) => item.id}
        style={styles.cryptoList}
      />
      <TouchableOpacity style={styles.addButton} onPress={pickFile}>
        <Ionicons name="add" size={24} color="white" />
      </TouchableOpacity>

      <Modal visible={isModalVisible} transparent={true} animationType="slide">
        <View style={styles.modalContainer}>
          <View style={styles.modalContent}>
            <Text style={{fontSize:16,marginBottom:15}}>Item: {selectedItem ? selectedItem.name : ''}</Text>
            <TouchableOpacity onPress={handleModalButtonPress} style={styles.buttonContainer2}>
        <LinearGradient
          colors={['#000000', '#000000']}
          style={styles.button2}
        >
          <Text style={styles.buttonText2}>DOWNLOAD</Text>
        </LinearGradient>
        </TouchableOpacity>

        <TouchableOpacity onPress={handleModalButtondelete} style={styles.buttonContainer2}>
        <LinearGradient
          colors={['#000000', '#000000']}
          style={styles.button2}
        >
          <Text style={styles.buttonText2}>DELETE</Text>
        </LinearGradient>
        </TouchableOpacity>
        <TouchableOpacity onPress={() => setModalVisible(false)} style={styles.buttonContainer2}>
        <LinearGradient
          colors={['#000000', '#000000']}
          style={styles.button2}
        >
          <Text style={styles.buttonText2}>CLOSE</Text>
        </LinearGradient>
        </TouchableOpacity>
          </View>
        </View>
      </Modal>
    </View>
  );
};




const styles1 = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f7fb',
    padding: 20,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 10,
  },
  icon: {
    fontSize: 24,
    color: '#b0b7c3',
  },
  title: {
    fontSize: 24,
    fontWeight: '500',
    color: '#333',
  },
  walletBalance: {
    backgroundColor: '#fff',
    borderRadius: 10,
    padding: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 5,
    marginBottom: 20,
  },
  walletIcon: {
    fontSize: 24,
    color: '#b0b7c3',
  },
  dropdown: {
    position: 'absolute',
    top: 20,
    right: 20,
    fontSize: 14,
    color: '#b0b7c3',
  },
  balanceTitle: {
    fontSize: 16,
    color: '#b0b7c3',
    marginVertical: 10,
  },
  balanceAmount: {
    fontSize: 32,
    fontWeight: '700',
    color: '#333',
  },
  balanceBtc: {
    fontSize: 14,
    color: '#b0b7c3',
  },
  balanceChange: {
    backgroundColor: '#e6f4ea',
    color: '#34c759',
    paddingVertical: 5,
    paddingHorizontal: 10,
    borderRadius: 20,
    fontSize: 14,
    fontWeight: '500',
    marginTop: 10,
  },
  arrow: {
    alignSelf: 'center',
    marginTop: 20,
    fontSize: 24,
    color: '#b0b7c3',
  },
  sorted: {
    fontSize: 14,
    color: '#b0b7c3',
    marginBottom: 10,
  },
  cryptoList: {
    backgroundColor: '#fff',
    borderRadius: 10,
    padding: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 5,
  },
  cryptoItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 10,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  cryptoItemLast: {
    borderBottomWidth: 0,
  },
  cryptoIcon: {
    fontSize: 24,
  },
  details: {
    flex: 1,
    marginLeft: 10,
  },
  cryptoName: {
    fontSize: 16,
    fontWeight: '500',
    color: '#333',
  },
  cryptoValue: {
    fontSize: 14,
    color: '#b0b7c3',
  },
  price: {
    alignItems: 'flex-end',
  },
  amount: {
    fontSize: 16,
    fontWeight: '500',
    color: '#333',
  },
  change: {
    fontSize: 14,
    fontWeight: '500',
  },
  positive: {
    color: '#34c759',
  },
  negative: {
    color: '#ff3b30',
  },
  footer: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    paddingVertical: 20,
    backgroundColor: '#fff',
    position: 'absolute',
    bottom: 0,
    width: '100%',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: -2 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 5,
  },
  footerIcon: {
    fontSize: 24,
    color: '#b0b7c3',
  },
});
const Tab = createBottomTabNavigator();
const Stack = createStackNavigator();

const MainTabs = () => (
  <Tab.Navigator
    screenOptions={({ route }) => ({
      tabBarIcon: ({ focused, color, size }) => {
        let iconName;

        if (route.name === 'Home') {
          iconName = focused ? 'home' : 'home-outline';
        } else if (route.name === 'ScanQR') {
          iconName = focused ? 'scan-sharp' : 'scan-outline';
        } else if (route.name === 'DisplayQR') {
          iconName = focused ? 'qr-code-sharp' : 'qr-code-outline';
        } else if (route.name === 'SendToId') {
          iconName = focused ? 'send' : 'send-outline';
        } else if (route.name === 'Settings') {
          iconName = focused ? 'settings' : 'settings-outline';
        }

        return <Ionicons name={iconName} size={size} color={color} />;
      },
      headerShown: false,
    })}
    tabBarOptions={{
      activeTintColor: 'black',
      inactiveTintColor: 'black',
      showLabel: false,
    }}
  >
    <Tab.Screen name="Home" component={HomeScreen} />
    <Tab.Screen name="ScanQR" component={ScanScreen} />
    <Tab.Screen name="DisplayQR" component={ReciScreen} />
    <Tab.Screen name="SendToId" component={Sendto} />
    <Tab.Screen name="Settings" component={Settings} />


  </Tab.Navigator>
);

const App = () => {
  return (
    <NavigationContainer>
      <Stack.Navigator initialRouteName="Login">
        <Stack.Screen name="Login" component={LoginScreen} options={{ headerShown: false }} />
        <Stack.Screen name="Main" component={MainTabs} options={{ headerShown: false }} />
        <Stack.Screen name="ss" component={SScreen} options={{ headerShown: false }} />
        <Stack.Screen name="login" component={loginn}options={{ headerShown: false }} />

      </Stack.Navigator>
    </NavigationContainer>
  );
};

const styles = StyleSheet.create({
  status: { padding: 16,
    color: "#0f0606",
  },
  container: {
    flex: 1,
    backgroundColor: '#fff',
  },
  walletLabel: {
    fontSize: 16,
    fontWeight: 'bold',
    padding: 16,
    
  },
  walletAddress: {
    fontSize: 14,
    marginLeft:16,
    marginBottom: 16
  },
  balance1: {
    
    marginLeft:15,
    marginRight:15,
    display: 'flex',
    flexDirection: 'row',
    borderWidth: 1,
    borderRadius:10,
    borderColor: '#AEAEAE',
    alignContent: 'center',
    justifyContent: 'center',
    
  },
  filesList: {
    borderWidth: 1,
    margin:15,
    flex: 1,
    padding: 16,
    borderColor: '#AEAEAE',
    borderRadius:10,
    borderBottomRightRadius:38
  },
  fileContainer: {
    display: 'flex',
    flexDirection: 'row',
    width:"98%",
    padding: 5,
    borderColor: '#AEAEAE',
    borderWidth: 1,
    margin:5,
    borderRadius:10,
    backgroundColor:"#AEAEAE"
  },
  fileName: {
    fontSize: 16,

  },
  addButton: {
    position: 'absolute',
    bottom: 16,
    right: 16,
    width: 76,
    height: 76,
    borderRadius: 38,
    backgroundColor: 'black',
    alignItems: 'center',
    justifyContent: 'center',
  },
  loginContainer: {

    flex: 1,
    alignItems: 'center',
    backgroundColor: '#fff',
  },
  loginLabel: {
    fontSize: 24,},

  backgroundImage: {
    flex: 1,
    resizeMode: 'cover', // or 'stretch'
  },

 
  scannerContainer: {
    justifyContent: 'center',
    alignItems: 'center',
    width: '90%',
    height: 491,  // Adjust the height as necessary
    marginBottom: 20,
    marginLeft: 5,
    borderWidth: 2,
    marginTop: 50,
    
  },
  cam:{

  },

  qrContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },

  container1: {
    flex: 1,
    alignItems: 'center',

    backgroundColor: '#fff',
  },
    container1: {
    flex: 1,
    alignItems: 'center',

    backgroundColor: '#fff',
  },
  label1: {
    fontSize: 18,
    marginBottom: 10,

  },
  address1: {
    fontSize: 12,
    fontWeight: 'bold',

  },
  input1: {
    height: 50,
    borderColor: 'gray',
    borderWidth: 1,
    borderRadius: 10,
    marginBottom: 20,
    width: '80%',
    paddingHorizontal: 10,
    fontSize: 18,
    textAlign: 'center',
    marginTop: 10,
  },
  buttonContainer1: {
    width: '80%',
    borderRadius: 10,
  },
  button1: {
    height: 50,
    justifyContent: 'center',
    alignItems: 'center',
    borderRadius: 10,
  },
  buttonText1: {
    color: '#fff',
    fontSize: 18,
    fontWeight: 'bold',
  },
  modalContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
  },
  modalContent: {
    width: '80%',
    borderRadius: 10,
    backgroundColor: 'white',
    padding: 20,
    borderRadius: 10,
    alignItems: 'center',
  },
  buttonContainer2: {
    width: '80%',
    borderRadius: 10,
    margin:5
  },
  button2: {
    height: 30,
    justifyContent: 'center',
    alignItems: 'center',
    borderRadius: 10,
  },
  buttonText2: {
    color: '#fff',
    fontSize: 12,
    fontWeight: 'bold',
  },
  buttonText3: {
    color: '#fff',
    fontSize: 18,
    fontWeight: 'bold',
    alignSelf: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
  },
  settings:{

    
  },
  cryptoList: {
    backgroundColor: '#fff',
    borderRadius: 10,
    padding: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 5,
    margin:15,
    borderBottomRightRadius:38
  },
  });

    export default App;