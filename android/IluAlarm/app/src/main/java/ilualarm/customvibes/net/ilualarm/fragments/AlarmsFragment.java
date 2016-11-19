package ilualarm.customvibes.net.ilualarm.fragments;

import android.content.Context;
import android.os.Bundle;
import android.support.design.widget.FloatingActionButton;
import android.support.design.widget.Snackbar;
import android.support.v4.app.Fragment;
import android.support.v7.widget.LinearLayoutManager;
import android.support.v7.widget.RecyclerView;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.Button;

import java.io.IOException;
import java.util.List;

import ilualarm.customvibes.net.ilualarm.R;
import ilualarm.customvibes.net.ilualarm.model.Alarm;
import ilualarm.customvibes.net.ilualarm.rest.IluAlarm;
import ilualarm.customvibes.net.ilualarm.rest.IluAlarmConnection;
import ilualarm.customvibes.net.ilualarm.rest.IluAlarmResponse;
import retrofit.Call;
import retrofit.Response;

/**
 * A fragment representing a list of Items.
 * <p/>
 * Activities containing this fragment MUST implement the {@link AlarmsFragmentListener}
 * interface.
 */
public class AlarmsFragment extends Fragment {

    private AlarmsFragmentListener mListener;
    private AlarmItemAdapter alarmsAdapter;
    private Button snzBtn;
    private RecyclerView listView;
    private IluAlarmConnection conn;
    private Button stopBtn;

    /**
     * Mandatory empty constructor for the fragment manager to instantiate the
     * fragment (e.g. upon screen orientation changes).
     */
    public AlarmsFragment() {
    }

    public static AlarmsFragment newInstance() {
        AlarmsFragment fragment = new AlarmsFragment();
        Bundle args = new Bundle();
        fragment.setArguments(args);
        return fragment;
    }

    @Override
    public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        if (getArguments() != null) {
        }
    }

    @Override
    public View onCreateView(LayoutInflater inflater, ViewGroup container,
                             Bundle savedInstanceState) {
        final View view = inflater.inflate(R.layout.fragment_alarm_list, container, false);

        FloatingActionButton fab = (FloatingActionButton) view.findViewById(R.id.fab);
        fab.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View view) {
                if (mListener != null) { mListener.addAlarm(); }
            }
        });

        snzBtn = (Button)view.findViewById(R.id.snooze_btn);
        snzBtn.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                conn.addCommand(new IluAlarmConnection.IluConnectionJob() {
                    @Override
                    public Response<IluAlarmResponse> doCall(IluAlarm conn) throws IOException {
                        Call<IluAlarmResponse> snooze = conn.snooze();
                        return snooze.execute();
                    }

                    @Override
                    public void onSuccess(Object data) {
                        getActivity().runOnUiThread(new Runnable() {
                            @Override
                            public void run() {
                                Snackbar.make(view, "Snoozed", Snackbar.LENGTH_LONG)
                                        .setAction("Action", null).show();
                            }
                        });
                    }

                    @Override
                    public void onError(Exception e) {
                        getActivity().runOnUiThread(new Runnable() {
                            @Override
                            public void run() {
                                Snackbar.make(view, "Error snoozing", Snackbar.LENGTH_LONG)
                                        .setAction("Action", null).show();
                            }
                        });
                    }
                });
            }
        });

        stopBtn = (Button)view.findViewById(R.id.stop_btn);
        stopBtn.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                conn.addCommand(new IluAlarmConnection.IluConnectionJob() {
                    @Override
                    public Response<IluAlarmResponse> doCall(IluAlarm conn) throws IOException {
                        Call<IluAlarmResponse> snooze = conn.stop();
                        return snooze.execute();
                    }

                    @Override
                    public void onSuccess(Object data) {
                        getActivity().runOnUiThread(new Runnable() {
                            @Override
                            public void run() {
                                Snackbar.make(view, "Stopped", Snackbar.LENGTH_LONG)
                                        .setAction("Action", null).show();
                            }
                        });
                    }

                    @Override
                    public void onError(Exception e) {
                        getActivity().runOnUiThread(new Runnable() {
                            @Override
                            public void run() {
                                Snackbar.make(view, "Error stopping", Snackbar.LENGTH_LONG)
                                        .setAction("Action", null).show();
                            }
                        });
                    }
                });
            }
        });

        listView = (RecyclerView) view.findViewById(R.id.alarm_list);

        // Set the adapter
        Context context = listView.getContext();
        listView.setLayoutManager(new LinearLayoutManager(context));
        alarmsAdapter = new AlarmItemAdapter(mListener);
        listView.setAdapter(alarmsAdapter);

        return view;
    }

    private void startUpdateTask() {

        conn.addCommand(new IluAlarmConnection.IluConnectionJob<List<Alarm>>() {

            @Override
            public Response doCall(IluAlarm conn) throws IOException {
                Call<IluAlarmResponse<List<Alarm>>> alarms = conn.getAlarms();
                return alarms.execute();
            }

            @Override
            public void onSuccess(final List<Alarm> alarms) {
                getActivity().runOnUiThread(new Runnable() {
                    @Override
                    public void run() {
                        if (alarmsAdapter != null) {
                            alarmsAdapter.setValues(alarms);
                        }
                    }
                });

                repeat(getContext(), conn);
            }

            @Override
            public void onError(Exception e) {
                retry(getContext(), conn);
            }
        });

    }

    @Override
    public void onResume() {
        super.onResume();

        conn = new IluAlarmConnection(getContext());
        startUpdateTask();
    }

    @Override
    public void onPause() {
        super.onPause();
        conn.purgeAll();
        conn = null;
    }

    @Override
    public void onAttach(Context context) {
        super.onAttach(context);
        if (context instanceof AlarmsFragmentListener) {
            mListener = (AlarmsFragmentListener) context;
        } else {
            throw new RuntimeException(context.toString()
                    + " must implement AlarmsFragmentListener");
        }
    }

    @Override
    public void onDetach() {
        super.onDetach();
        mListener = null;
    }

    /**
     * This interface must be implemented by activities that contain this
     * fragment to allow an interaction in this fragment to be communicated
     * to the activity and potentially other fragments contained in that
     * activity.
     * <p/>
     * See the Android Training lesson <a href=
     * "http://developer.android.com/training/basics/fragments/communicating.html"
     * >Communicating with Other Fragments</a> for more information.
     */
    public interface AlarmsFragmentListener {
        void addAlarm();
        void editAlarm(Alarm alarm);
    }
}
