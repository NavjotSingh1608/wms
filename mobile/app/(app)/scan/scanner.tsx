import { useState, useRef } from 'react';
import { View, StyleSheet, Dimensions, Alert } from 'react-native';
import { Text, Button, IconButton } from 'react-native-paper';
import { CameraView, useCameraPermissions } from 'expo-camera';
import { useRouter } from 'expo-router';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { Colors } from '@/constants/colors';

const { width: SCREEN_WIDTH } = Dimensions.get('window');
const SCAN_AREA = SCREEN_WIDTH * 0.7;

export default function ScannerScreen() {
  const router = useRouter();
  const [permission, requestPermission] = useCameraPermissions();
  const [scanned, setScanned] = useState(false);
  const [torch, setTorch] = useState(false);

  const handleBarCodeScanned = ({ data }: { data: string }) => {
    if (scanned) return;
    setScanned(true);

    const match = data.match(/^WMS:GRN:(.+)$/);
    if (match) {
      const grnId = match[1];
      router.replace(`/(app)/grn/${grnId}` as any);
    } else {
      Alert.alert(
        'Invalid QR Code',
        'This QR code is not a valid WMS label. Expected format: WMS:GRN:{id}',
        [{ text: 'Scan Again', onPress: () => setScanned(false) }],
      );
    }
  };

  if (!permission) {
    return (
      <View style={styles.center}>
        <Text variant="bodyLarge">Requesting camera permission...</Text>
      </View>
    );
  }

  if (!permission.granted) {
    return (
      <View style={styles.center}>
        <MaterialCommunityIcons name="camera-off" size={64} color={Colors.textSecondary} />
        <Text variant="titleMedium" style={{ marginTop: 16, fontWeight: '600' }}>
          Camera Permission Required
        </Text>
        <Text variant="bodyMedium" style={{ color: Colors.textSecondary, textAlign: 'center', marginTop: 8, paddingHorizontal: 32 }}>
          WMS needs camera access to scan QR codes on material labels.
        </Text>
        <Button mode="contained" onPress={requestPermission} style={{ marginTop: 20, borderRadius: 8 }}>
          Grant Permission
        </Button>
        <Button mode="text" onPress={() => router.back()} style={{ marginTop: 8 }}>
          Go Back
        </Button>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <CameraView
        style={StyleSheet.absoluteFillObject}
        facing="back"
        enableTorch={torch}
        barcodeScannerSettings={{ barcodeTypes: ['qr'] }}
        onBarcodeScanned={scanned ? undefined : handleBarCodeScanned}
      />

      {/* Overlay */}
      <View style={styles.overlay}>
        {/* Top bar */}
        <View style={styles.topBar}>
          <IconButton icon="arrow-left" iconColor="#fff" size={28} onPress={() => router.back()} />
          <Text variant="titleMedium" style={{ color: '#fff', fontWeight: '600' }}>
            Scan QR Code
          </Text>
          <IconButton
            icon={torch ? 'flashlight' : 'flashlight-off'}
            iconColor="#fff"
            size={28}
            onPress={() => setTorch((t) => !t)}
          />
        </View>

        {/* Scan window mask */}
        <View style={styles.maskRow}>
          <View style={styles.maskSide} />
          <View style={styles.scanWindow}>
            {/* Corner indicators */}
            <View style={[styles.corner, styles.cornerTL]} />
            <View style={[styles.corner, styles.cornerTR]} />
            <View style={[styles.corner, styles.cornerBL]} />
            <View style={[styles.corner, styles.cornerBR]} />
          </View>
          <View style={styles.maskSide} />
        </View>

        {/* Bottom */}
        <View style={styles.bottom}>
          <Text variant="bodyMedium" style={{ color: '#fff', textAlign: 'center' }}>
            Align the QR code within the frame
          </Text>
          {scanned && (
            <Button mode="contained" onPress={() => setScanned(false)} style={{ marginTop: 16, borderRadius: 8 }}>
              Scan Again
            </Button>
          )}
        </View>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#000' },
  center: { flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: Colors.background },
  overlay: { ...StyleSheet.absoluteFillObject, justifyContent: 'space-between' },
  topBar: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingTop: 50,
    paddingHorizontal: 8,
    backgroundColor: 'rgba(0,0,0,0.5)',
  },
  maskRow: { flexDirection: 'row', alignItems: 'center' },
  maskSide: { flex: 1, backgroundColor: 'rgba(0,0,0,0.6)' },
  scanWindow: {
    width: SCAN_AREA,
    height: SCAN_AREA,
    borderRadius: 16,
    position: 'relative',
  },
  corner: {
    position: 'absolute',
    width: 30,
    height: 30,
    borderColor: '#fff',
    borderWidth: 3,
  },
  cornerTL: { top: 0, left: 0, borderRightWidth: 0, borderBottomWidth: 0, borderTopLeftRadius: 16 },
  cornerTR: { top: 0, right: 0, borderLeftWidth: 0, borderBottomWidth: 0, borderTopRightRadius: 16 },
  cornerBL: { bottom: 0, left: 0, borderRightWidth: 0, borderTopWidth: 0, borderBottomLeftRadius: 16 },
  cornerBR: { bottom: 0, right: 0, borderLeftWidth: 0, borderTopWidth: 0, borderBottomRightRadius: 16 },
  bottom: {
    alignItems: 'center',
    paddingBottom: 60,
    paddingHorizontal: 32,
    backgroundColor: 'rgba(0,0,0,0.5)',
    paddingTop: 20,
  },
});
