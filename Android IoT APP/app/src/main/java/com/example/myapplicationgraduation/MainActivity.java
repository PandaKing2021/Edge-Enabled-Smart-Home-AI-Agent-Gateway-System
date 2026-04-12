package com.example.myapplicationgraduation;

import android.app.Activity;
import android.content.Intent;
import android.database.sqlite.SQLiteDatabase;
import android.os.Bundle;
import android.view.View;
import android.widget.Button;
import android.widget.Toast;

public class MainActivity extends Activity {
    private Button b_AirConditioner_detail;
    private Button b_Curtain_detail;
    private Button b_Door_security_detail;
    private Button b_history;
    private SQLiteDatabase db;
    private DatabaseHelper databaseHelper;

    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);
        setTitle("Main Page");

        DatabaseHelper databaseHelper = new DatabaseHelper(this,"iot_db",null,1);
        db = databaseHelper.getWritableDatabase();

        b_AirConditioner_detail = (Button)findViewById(R.id.light_detail);
        b_Curtain_detail = (Button)findViewById(R.id.curtain_detail);
        b_Door_security_detail = (Button)findViewById(R.id.door_security_detail);
        b_history = (Button)findViewById(R.id.to_hiatory_list);

        b_AirConditioner_detail.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View view) {
                Toast.makeText(MainActivity.this,"Navigate to Smart Air Conditioner Details",Toast.LENGTH_LONG).show();
                startActivity(new Intent(MainActivity.this, AirConditionerActivity.class));
            }
        });

        b_Curtain_detail.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View view) {
                Toast.makeText(MainActivity.this,"Navigate to Smart Curtain Details",Toast.LENGTH_LONG).show();
                startActivity(new Intent(MainActivity.this, CurtainActivity.class));
            }
        });

        b_Door_security_detail.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View view) {
                Toast.makeText(MainActivity.this,"Navigate to Smart Door Lock Details",Toast.LENGTH_LONG).show();
                startActivity(new Intent(MainActivity.this, DoorSecurityActivity.class));
            }
        });

        b_history.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View view) {
                Toast.makeText(MainActivity.this,"Navigate to History Details",Toast.LENGTH_LONG).show();
                startActivity(new Intent(MainActivity.this, HistoryActivity.class));
            }
        });


    }
}
