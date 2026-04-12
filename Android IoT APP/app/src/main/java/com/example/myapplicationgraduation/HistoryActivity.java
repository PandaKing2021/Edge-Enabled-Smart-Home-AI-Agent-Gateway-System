package com.example.myapplicationgraduation;

import android.annotation.SuppressLint;
import android.app.Activity;
import android.content.Intent;
import android.database.Cursor;
import android.database.sqlite.SQLiteDatabase;
import android.os.Bundle;
import android.view.View;
import android.widget.Button;
import android.widget.ListView;
import android.widget.SimpleAdapter;
import android.widget.Toast;

import java.text.ParseException;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Date;
import java.util.HashMap;
import java.util.List;

public class HistoryActivity extends Activity {
    private SQLiteDatabase db;
    private DatabaseHelper databaseHelper;
    private ListView l_history_list;
    private Button b_back;
    private Button b_refresh;
    private String[] data = {"NULL","NULL","NULL","NULL"};

    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_history);
        setTitle("数据接收历史记录");

        DatabaseHelper databaseHelper = new DatabaseHelper(this,"iot_db",null,1);
        db = databaseHelper.getWritableDatabase();

        b_back = (Button)findViewById(R.id.back_to_main);
        b_refresh = (Button)findViewById(R.id.refresh);
        l_history_list = (ListView)findViewById(R.id.history_list);

        b_back.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View view) {
                Toast.makeText(HistoryActivity.this,"返回至主菜单",Toast.LENGTH_LONG).show();
                startActivity(new Intent(HistoryActivity.this, MainActivity.class));
            }
        });

        b_refresh.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View view) {
                try {
                    refreshViews();
                } catch (ParseException e) {
                    throw new RuntimeException(e);
                }
            }
        });

    }

    @SuppressLint("Range")
    private void refreshViews() throws ParseException {
        List<HashMap<String,Object>> data_list = new ArrayList<HashMap<String,Object>>();
        SimpleDateFormat format = new SimpleDateFormat("yyyy - MM - dd HH:mm:ss");
        Date time = new Date();
        String d = format.format(time);
        Date date = null;
        try {
            date = format.parse(d);
        }catch (Exception e){
            e.printStackTrace();
        }

        Cursor cursor = db.query("history_data", null, null, null, null, null, null);
        int light_th = 0;
        float temperature = 0.0F;
        float humidity = 0.0F;
        float brightness = 0.0F;

        if (cursor.moveToFirst()) {
            do {
                //遍历Cursor对象
                int date_temp = cursor.getInt(cursor.getColumnIndexOrThrow("time"));
                temperature = cursor.getFloat(cursor.getColumnIndexOrThrow("temperature"));
                humidity = cursor.getFloat(cursor.getColumnIndexOrThrow("humidity"));
                brightness = cursor.getFloat(cursor.getColumnIndexOrThrow("brightness"));

                // 加入list
                HashMap<String,Object>item = new HashMap<String,Object>();
                item.put("time",date);
                item.put("temperature", temperature);
                item.put("humidity", humidity);
                item.put("brightness", brightness);
                data_list.add(item);
            } while (cursor.moveToNext());
        }
        cursor.close();

        SimpleAdapter adapter = new SimpleAdapter(getApplicationContext(), data_list, R.layout.list_content, new String[]{"time","temperature","humidity","brightness"}, new int[]{R.id.column_time,R.id.column_temperature,R.id.column_humidity,R.id.column_brightness});

        l_history_list.setAdapter(adapter);
    }
}
