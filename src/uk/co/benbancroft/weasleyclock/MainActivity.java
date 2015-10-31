package uk.co.benbancroft.weasleyclock;

import android.app.Activity;
import android.app.ActivityManager;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.os.Bundle;
import android.os.StrictMode;
import android.preference.PreferenceManager;
import android.view.View;
import android.widget.Button;
import android.widget.CompoundButton;
import android.widget.EditText;
import android.widget.ToggleButton;

import static uk.co.benbancroft.weasleyclock.R.id.addressText;
import static uk.co.benbancroft.weasleyclock.R.id.intervalText;
import static uk.co.benbancroft.weasleyclock.R.id.portText;

public class MainActivity extends Activity {

    SharedPreferences preferences;
    EditText addressField;
    EditText portField;
    EditText intervalField;
    ToggleButton startButton;
    Intent service;

    private boolean isMyServiceRunning(Class<?> serviceClass) {
        ActivityManager manager = (ActivityManager) getSystemService(Context.ACTIVITY_SERVICE);
        for (ActivityManager.RunningServiceInfo service : manager.getRunningServices(Integer.MAX_VALUE)) {
            if (serviceClass.getName().equals(service.service.getClassName())) {
                return true;
            }
        }
        return false;
    }

    @Override
    protected void onResume() {
        super.onResume();

        if (isMyServiceRunning(LocationService.class)){
            startButton.setChecked(true);
        }
    }

    /**
     * Called when the activity is first created.
     */
    @Override
    public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.main);

        preferences = PreferenceManager.getDefaultSharedPreferences(this);
        addressField = (EditText) findViewById(addressText);
        portField = (EditText) findViewById(portText);
        intervalField = (EditText) findViewById(intervalText);

        addressField.setText(preferences.getString("address", null));
        portField.setText(Integer.toString(preferences.getInt("port", 8080)));
        intervalField.setText(Integer.toString(preferences.getInt("interval", 10)));

        startButton = (ToggleButton) findViewById(R.id.startButton);

        service = new Intent(this, LocationService.class);
        startButton.setOnCheckedChangeListener(new CompoundButton.OnCheckedChangeListener() {
            public void onCheckedChanged(CompoundButton buttonView, boolean isChecked) {
                if (isChecked) {

                    /*service.putExtra("address", addressField.getText().toString());
                    service.putExtra("port", Integer.parseInt(portField.getText().toString()));
                    service.putExtra("interval", Integer.parseInt(intervalField.getText().toString()));*/
                    updatePreferences();

                    System.out.println("Starting service act");
                    startService(service);
                } else {
                    stopService(service);
                }
            }
        });

    }

    private void updatePreferences(){
        SharedPreferences.Editor editor = preferences.edit();

        editor.putString("address", addressField.getText().toString());
        editor.putInt("port", Integer.parseInt(portField.getText().toString()));
        editor.putInt("interval", Integer.parseInt(intervalField.getText().toString()));
        editor.commit();
    }

    @Override
    protected void onStop() {
        super.onStop();

        updatePreferences();

    }
}
