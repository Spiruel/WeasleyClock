package uk.co.benbancroft.weasleyclock;

import android.app.Notification;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.app.Service;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.location.Location;
import android.location.LocationManager;
import android.os.Bundle;
import android.os.Handler;
import android.os.IBinder;
import android.os.StrictMode;
import android.preference.PreferenceManager;
import android.widget.Toast;

import java.io.DataOutputStream;
import java.io.IOException;
import java.net.InetSocketAddress;
import java.net.ServerSocket;
import java.net.Socket;
import java.net.UnknownHostException;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.Timer;
import java.util.TimerTask;

public class LocationService extends Service {

    private static final int NOTIFICATION_ID = 1;

    private Handler handler = new Handler();
    private Timer timer = null;

    private String address;
    private int port;
    private int interval;

    private Date lastUpdated = null;
    private String errorMessage = null;

    private NotificationManager notificationManager;
    private Notification.Builder builder;


    WeasleyLocationListener locationListener;
    LocationManager locationManager;

    @Override
    public IBinder onBind(Intent intent) {
        return null;
    }

    @Override
    public void onDestroy() {
        super.onDestroy();

        timer.cancel();
        notificationManager.cancel(NOTIFICATION_ID);


    }

    private String getNoficationMessage(){
        String lastUpdatedString = getLastUpdated();
        if (errorMessage != null){
            return errorMessage;
        }else if (lastUpdatedString != null) return "Last Updated: " + lastUpdatedString;
        else return "Connecting to " + this.address + " on port " + this.port + " every " + this.interval + " seconds";
    }

    private void createNotification(){

        builder = new Notification.Builder(this);
        builder.setSmallIcon(R.drawable.ic_launcher);
        builder.setContentTitle("WeasleyClock");

        String message = getNoficationMessage();
        builder.setContentText(message);
        builder.setTicker(message);

        final Intent notificationIntent = new Intent(this, MainActivity.class);
        final PendingIntent pi = PendingIntent.getActivity(this, 0,
                notificationIntent, 0);
        builder.setContentIntent(pi);
        final Notification notification = builder.build();

        //return notification;
    }

    public void updateNotification(){
        String message = getNoficationMessage();
        builder.setContentText(message);
        notificationManager.notify(NOTIFICATION_ID, builder.build());
    }

    @Override
    public void onCreate() {

        notificationManager = (NotificationManager) getSystemService(Context.NOTIFICATION_SERVICE);
        locationManager = (LocationManager) getSystemService(Context.LOCATION_SERVICE);

        System.out.println("Starting service create");
    }

    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {

        //Bundle extras = intent.getExtras();

        StrictMode.ThreadPolicy policy = new StrictMode.ThreadPolicy.Builder().permitAll().build();
        StrictMode.setThreadPolicy(policy);

        SharedPreferences preferences = PreferenceManager.getDefaultSharedPreferences(this);

        System.out.println("Starting service");

        this.address = preferences.getString("address", null);
        this.port = preferences.getInt("port", 8080);
        this.interval = preferences.getInt("interval", 10);

        /*this.address = extras.getString("address");
        this.port = extras.getInt("port");
        this.interval = extras.getInt("interval");*/

        createNotification();
        notificationManager.notify(NOTIFICATION_ID, builder.build());


        this.locationListener = new WeasleyLocationListener();
        locationManager.requestLocationUpdates(LocationManager.GPS_PROVIDER, this.interval * 1000, 10, locationListener);

        // schedule task
        if (timer != null) {
            timer.cancel();
        }
        timer = new Timer();
        timer.scheduleAtFixedRate(new TimeDisplayTimerTask(), 0, this.interval * 1000);

        return Service.START_STICKY;
    }

    private String getLastUpdated() {
        if (lastUpdated == null) return null;
        // get date time in custom format
        SimpleDateFormat sdf = new SimpleDateFormat("yyyy/MM/dd - HH:mm:ss");
        return sdf.format(lastUpdated);
    }


    class TimeDisplayTimerTask extends TimerTask {

        @Override
        public void run() {
            // run on another thread
            handler.post(new Runnable() {

                @Override
                public void run() {

                    try {
                        Location location = locationListener.getNewLocation();
                        if (location != null) {
                            Socket socket = new Socket();
                            socket.connect(new InetSocketAddress(address, port), 1000);
                            DataOutputStream outStream = new DataOutputStream(socket.getOutputStream());

                            StringBuilder locationMessage = new StringBuilder();
                            locationMessage.append(location.getLatitude());
                            locationMessage.append(":");
                            locationMessage.append(location.getLongitude());
                            locationMessage.append(":");
                            locationMessage.append(location.getAccuracy());
                            locationMessage.append(":__tc15__");

                            outStream.writeBytes(locationMessage.toString() + "\n");
                            //outStream.writeBytes("test" + "__tc15__\n");


                            socket.close();

                            errorMessage = null;
                            lastUpdated = new Date();

                            updateNotification();
                        }

                    } catch (UnknownHostException e) {
                        errorMessage = "Error: Unknown host " + address;
                        updateNotification();

                    } catch (IOException e) {
                        errorMessage = "Error: " + e.getMessage();
                        updateNotification();
                    }

                    // display debug toast

                    /*Toast.makeText(getApplicationContext(), getNoficationMessage(),
                            Toast.LENGTH_SHORT).show();*/

                }

            });
        }

    }

}