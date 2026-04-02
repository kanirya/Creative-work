import * as Notifications from 'expo-notifications';
import { Platform } from 'react-native';

// Configure notification behavior
Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldShowAlert: true,
    shouldPlaySound: true,
    shouldSetBadge: true,
  }),
});

export async function registerForPushNotifications(): Promise<string | null> {
  if (Platform.OS === 'android') {
    await Notifications.setNotificationChannelAsync('default', {
      name: 'default',
      importance: Notifications.AndroidImportance.MAX,
      vibrationPattern: [0, 250, 250, 250],
      lightColor: '#3b82f6',
    });
  }

  const { status: existingStatus } = await Notifications.getPermissionsAsync();
  let finalStatus = existingStatus;

  if (existingStatus !== 'granted') {
    const { status } = await Notifications.requestPermissionsAsync();
    finalStatus = status;
  }

  if (finalStatus !== 'granted') {
    return null;
  }

  const token = (await Notifications.getExpoPushTokenAsync()).data;
  return token;
}

export async function scheduleAssignmentNotification(
  assignmentTitle: string,
  dueDate: Date
) {
  // Schedule notification 24 hours before due date
  const notificationDate = new Date(dueDate.getTime() - 24 * 60 * 60 * 1000);

  await Notifications.scheduleNotificationAsync({
    content: {
      title: 'Assignment Due Tomorrow',
      body: `${assignmentTitle} is due tomorrow`,
      data: { type: 'assignment' },
    },
    trigger: notificationDate,
  });
}

export async function sendAnnouncementNotification(
  title: string,
  message: string
) {
  await Notifications.scheduleNotificationAsync({
    content: {
      title: `New Announcement: ${title}`,
      body: message,
      data: { type: 'announcement' },
    },
    trigger: null, // Send immediately
  });
}
