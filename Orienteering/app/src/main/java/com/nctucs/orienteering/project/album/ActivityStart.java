package com.nctucs.orienteering.project.album;

///////////////////////////STUDENT//////////////////////////
///////////// 姓名:林鈺璇 /////////////////////////////////
///////////// 學號:0116224 //////////////////////////////
//////////////////////////////////////////////////////////////////
import java.util.Random;

import android.app.Activity;
import android.content.Intent;
import android.content.SharedPreferences;
import android.os.Bundle;
import android.os.Message;
import android.util.Log;
import android.widget.ListView;
import android.widget.ProgressBar;

import com.nctucs.orienteering.project.JSONMsg.JSONType;
import com.nctucs.orienteering.project.R;
import com.nctucs.orienteering.project.tcpSocket.tcpSocket;

import org.json.JSONObject;

public class ActivityStart extends Activity {

    ListView lv;
    ProgressBar loadingBar = null;
    SharedPreferences userData = null;
    String token;
    boolean isNewGame = false;
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_start);
        userData = getSharedPreferences("userData", MODE_PRIVATE);
        token = userData.getString("token", null);
        if(token == null){
            isNewGame = true;
            new GetTokenThread().start();
            Log.e("new token", token);
            userData.edit().putString("token", token).apply();
        }else{
            isNewGame = false;
            Log.e("token", token);
        }
        loadingBar = (ProgressBar)findViewById( R.id.progress_bar );
    }

    private class GetTokenThread extends Thread implements Runnable{
        @Override
        public void run () {
            try {
                tcpSocket socket = new tcpSocket();
                socket.send(new JSONType(-1));

                JSONObject result = socket.recieve();
                token = result.getString("token");
            }
            catch ( Exception e ){
                e.printStackTrace();
            }


        }
    }

    @Override
    protected void onResume() {
        super.onResume();

        new Thread( new Runnable() {
            @Override
            public void run() {

                Random random = new Random();
                for ( int i = 10 ; i <= 100 ; i += random.nextInt() % 5 + 5 ){
                    try{
                        Thread.sleep( 300 , 0 );
                    }
                    catch ( Exception e ){
                        e.printStackTrace();
                    }
                    loadingBar.setProgress( i );

                }

                if(isNewGame){
                    Intent intent = new Intent(ActivityStart.this, ActivitySaveLoad.class);
                    startActivity(intent);
                }

            }
        } ).start();

    }
}
