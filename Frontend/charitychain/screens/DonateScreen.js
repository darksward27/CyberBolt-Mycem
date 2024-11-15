import React from 'react';
import { View, StyleSheet, ScrollView, Image } from 'react-native';
import { Text, Button, Avatar, Card } from 'react-native-paper';
import { useSelector } from 'react-redux';
import { SafeAreaView } from 'react-native-safe-area-context';
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

const HomeScreen = () => {
    const [to_address, setto] = useState('');


    useFocusEffect(
        useCallback(() => {
        let subcription;
        const getbalance = async() => {
            subcription = await sendMessage('check_balance', {wall});
            balance = String(subcription['result']);
            setto(balance);
    }
        getbalance();
        return () => {  }
        }, [])
    );


const CategoryIcon = ({ icon, label }) => (
    <View style={styles.categoryItem}>
      <View style={styles.categoryIcon}>
        <IconButton icon={icon} color="white" size={24} />
      </View>
      <Text style={styles.categoryLabel}>{label}</Text>
    </View>
  );

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView>
        <View style={styles.header}>
          <Text style={styles.headerText}>Hello good people</Text>
          <Avatar.Text size={32} label="J" />
        </View>

        <Card style={styles.walletCard}>
          <Card.Content style={styles.walletContent}>
            <View style={styles.walletInfo}>
              <Avatar.Icon size={32} icon="wallet" style={styles.walletIcon} />
              <View>
                <Text>Joel's Wallet</Text>
                <Text style={styles.balance}>${to_address}</Text>
              </View>
            </View>
            <Button mode="contained" style={styles.topUpButton}>
              Top up
            </Button>
          </Card.Content>
        </Card>

        <View style={styles.categories}>
          <CategoryIcon icon="book" label="Education" />
          <CategoryIcon icon="heart-pulse" label="Medicine" />
          <CategoryIcon icon="account-group" label="Human" />
          <CategoryIcon icon="grid" label="Others" />
        </View>

        <Text style={styles.sectionTitle}>Help them smile again</Text>
        <Card style={styles.imageCard}>
          <Card.Cover
            source={{
              uri: 'https://images.unsplash.com/photo-1488521787991-ed7bbaae773c?w=800',
            }}
          />
        </Card>
      </ScrollView>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#ffffff',
    padding: 16,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 24,
  },
  headerText: {
    fontSize: 18,
    fontWeight: '500',
    color: '#1a75ff',
  },
  walletCard: {
    backgroundColor: '#FFE5B4',
    marginBottom: 32,
  },
  walletContent: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  walletInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  walletIcon: {
    backgroundColor: '#ffffff',
  },
  balance: {
    fontSize: 18,
    fontWeight: 'bold',
  },
  topUpButton: {
    backgroundColor: '#1a1a1a',
  },
  categories: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 32,
  },
  categoryItem: {
    alignItems: 'center',
    gap: 8,
  },
  categoryIcon: {
    backgroundColor: '#1a1a1a',
    borderRadius: 24,
    width: 48,
    height: 48,
    justifyContent: 'center',
    alignItems: 'center',
  },
  categoryLabel: {
    fontSize: 12,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '500',
    marginBottom: 16,
  },
  imageCard: {
    marginBottom: 32,
  },
});

export default HomeScreen;
