package ilualarm.customvibes.net.ilualarm.fragments;

import android.app.DatePickerDialog;
import android.app.TimePickerDialog;
import android.content.Context;
import android.os.Bundle;
import android.support.design.widget.Snackbar;
import android.support.v4.app.Fragment;
import android.text.TextUtils;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.ArrayAdapter;
import android.widget.Button;
import android.widget.CheckBox;
import android.widget.CompoundButton;
import android.widget.DatePicker;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.Spinner;
import android.widget.TextView;
import android.widget.TimePicker;

import java.io.IOException;
import java.text.SimpleDateFormat;
import java.util.Calendar;

import ilualarm.customvibes.net.ilualarm.R;
import ilualarm.customvibes.net.ilualarm.model.Alarm;
import ilualarm.customvibes.net.ilualarm.rest.IluAlarm;
import ilualarm.customvibes.net.ilualarm.rest.IluAlarmConnection;
import ilualarm.customvibes.net.ilualarm.rest.IluAlarmResponse;
import retrofit.Call;
import retrofit.Response;

/**
 * A simple {@link Fragment} subclass.
 * Activities that contain this fragment must implement the
 * {@link AlarmFragmentListener} interface
 * to handle interaction events.
 * Use the {@link AlarmFragment#newInstance} factory method to
 * create an instance of this fragment.
 */
public class AlarmFragment extends Fragment {

    private static final String ARG_ALARM = "alarm";
    private Alarm alarm;

    private AlarmFragmentListener mListener;
    private Calendar calendar;
    private TextView scheduledTime;
    private TextView scheduledDate;
    private CheckBox enabled;

    public AlarmFragment() {
        // Required empty public constructor
    }

    public static AlarmFragment newInstance() {
        return newInstance(null);
    }

    public static AlarmFragment newInstance(Alarm alarm) {
        AlarmFragment fragment = new AlarmFragment();
        Bundle args = new Bundle();
        args.putSerializable(ARG_ALARM, alarm);
        fragment.setArguments(args);
        return fragment;
    }

    @Override
    public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        if (getArguments() != null) {
            alarm = (Alarm) getArguments().getSerializable(ARG_ALARM);
        }
    }

    private void openDatePicker() {
        final DatePickerDialog datePickerDialog = new DatePickerDialog(getContext(), new DatePickerDialog.OnDateSetListener() {
            @Override
            public void onDateSet(DatePicker view, int year, int monthOfYear, int dayOfMonth) {
                calendar.set(Calendar.YEAR, year);
                calendar.set(Calendar.MONTH, monthOfYear);
                calendar.set(Calendar.DAY_OF_MONTH, dayOfMonth);
                SimpleDateFormat formatDate = new SimpleDateFormat("d/M/y");
                scheduledDate.setText(formatDate.format(calendar.getTime()));
                enabled.setChecked(true);
            }
        }, calendar.get(Calendar.YEAR), calendar.get(Calendar.MONTH), calendar.get(Calendar.DAY_OF_MONTH));
        datePickerDialog.show();
    }

    private void openTimePicker() {

        final TimePickerDialog timePickerDialog = new TimePickerDialog(getContext(), new TimePickerDialog.OnTimeSetListener() {
            @Override
            public void onTimeSet(TimePicker view, int hourOfDay, int minute) {
                calendar.set(Calendar.HOUR_OF_DAY, hourOfDay);
                calendar.set(Calendar.MINUTE, minute);

                SimpleDateFormat formatTime = new SimpleDateFormat("H:m");
                scheduledTime.setText(formatTime.format(calendar.getTime()));
                enabled.setChecked(true);

            }
        }, calendar.get(Calendar.HOUR_OF_DAY), calendar.get(Calendar.MINUTE), true);

        timePickerDialog.show();
    }

    @Override
    public View onCreateView(LayoutInflater inflater, ViewGroup container,
                             Bundle savedInstanceState) {

        SimpleDateFormat formatDate = new SimpleDateFormat("d/M/y");
        SimpleDateFormat formatTime = new SimpleDateFormat("H:m");


        // Inflate the layout for this fragment
        final View view = inflater.inflate(R.layout.fragment_alarm, container, false);

        final Button btnTimer = (Button) view.findViewById(R.id.btn_timer);
        final Button btnScheduled = (Button) view.findViewById(R.id.btn_scheduled);

        final LinearLayout lytTimer = (LinearLayout) view.findViewById(R.id.lyt_type_timer);
        final LinearLayout lytScheduled = (LinearLayout) view.findViewById(R.id.lyt_type_scheduled);
        enabled = (CheckBox)view.findViewById(R.id.enabled);
        final Button btnSave = (Button) view.findViewById(R.id.btn_save);

        final Spinner spinner = (Spinner) view.findViewById(R.id.repeat_spinner);
        ArrayAdapter<CharSequence> adapter = ArrayAdapter.createFromResource(getActivity(),
                R.array.repeat_options, android.R.layout.simple_spinner_item);
        adapter.setDropDownViewResource(android.R.layout.simple_spinner_dropdown_item);
        spinner.setAdapter(adapter);
        final CheckBox scheduleRepeat = (CheckBox) view.findViewById(R.id.scheduled_repeat);

        calendar = Calendar.getInstance();
        calendar.set(Calendar.SECOND, 0);
        calendar.set(Calendar.MILLISECOND, 1);

        if (alarm == null) {
            btnTimer.setOnClickListener(new View.OnClickListener() {
                @Override
                public void onClick(View v) {
                    lytScheduled.setVisibility(View.GONE);
                    lytTimer.setVisibility(View.VISIBLE);
                }
            });

            btnScheduled.setOnClickListener(new View.OnClickListener() {
                @Override
                public void onClick(View v) {
                    lytTimer.setVisibility(View.GONE);
                    lytScheduled.setVisibility(View.VISIBLE);
                }
            });
            enabled.setChecked(true);
            enabled.setEnabled(false);

        }
        else {
            enabled.setChecked(alarm.isEnabled());
            enabled.setEnabled(true);

            if (alarm.getType() == Alarm.TYPE_ALARM) {
                lytScheduled.setVisibility(View.GONE);
                lytTimer.setVisibility(View.VISIBLE);
                EditText timeoutTxt = (EditText) view.findViewById(R.id.timer_timeout);
                timeoutTxt.setText(String.valueOf(alarm.getTimeout()));
                EditText messageTxt = (EditText) view.findViewById(R.id.timer_message);
                messageTxt.setText(alarm.getMessage());
            }
            else {
                lytTimer.setVisibility(View.GONE);
                lytScheduled.setVisibility(View.VISIBLE);

                EditText messageTxt = (EditText) view.findViewById(R.id.scheduled_message);
                messageTxt.setText(alarm.getMessage());

                if (alarm.getTime() != null) {
                    calendar.setTime(alarm.getTime());
                }
                else {
                    calendar.setTime(alarm.getSetTime());
                }

                Integer rep = alarm.getRepeatEvery();
                scheduleRepeat.setChecked(rep != null);
                spinner.setEnabled(rep != null);
                if (rep != null) {
                    spinner.setSelection(getSpinnerPosition(alarm));
                }

            }

        }

        scheduledTime = (TextView)view.findViewById(R.id.scheduled_time);
        scheduledTime.setFocusable(false);

        scheduledDate = (TextView)view.findViewById(R.id.scheduled_date);
        scheduledDate.setFocusable(false);

        scheduleRepeat.setOnCheckedChangeListener(new CompoundButton.OnCheckedChangeListener() {
            @Override
            public void onCheckedChanged(CompoundButton buttonView, boolean isChecked) {
                spinner.setEnabled(isChecked);
            }
        });

        spinner.setEnabled(false);



        scheduledDate.setText(formatDate.format(calendar.getTime()));
        scheduledTime.setText(formatTime.format(calendar.getTime()));

        scheduledDate.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                openDatePicker();
            }
        });

        scheduledTime.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                openTimePicker();
            }
        });

/*
        final DatePickerDialog datePickerDialog = DatePickerDialog.newInstance(this, calendar.get(Calendar.YEAR), calendar.get(Calendar.MONTH), calendar.get(Calendar.DAY_OF_MONTH), isVibrate());
        final TimePickerDialog timePickerDialog = TimePickerDialog.newInstance(this, calendar.get(Calendar.HOUR_OF_DAY), calendar.get(Calendar.MINUTE), false, false);

        findViewById(R.id.dateButton).setOnClickListener(new OnClickListener() {

            @Override
            public void onClick(View v) {
                datePickerDialog.setVibrate(isVibrate());
                datePickerDialog.setYearRange(1985, 2028);
                datePickerDialog.setCloseOnSingleTapDay(isCloseOnSingleTapDay());
                datePickerDialog.show(getSupportFragmentManager(), DATEPICKER_TAG);
            }
        });

        findViewById(R.id.timeButton).setOnClickListener(new OnClickListener() {
            @Override
            public void onClick(View v) {
                timePickerDialog.setVibrate(isVibrate());
                timePickerDialog.setCloseOnSingleTapMinute(isCloseOnSingleTapMinute());
                timePickerDialog.show(getSupportFragmentManager(), TIMEPICKER_TAG);
            }
        });

        if (savedInstanceState != null) {
            DatePickerDialog dpd = (DatePickerDialog) getSupportFragmentManager().findFragmentByTag(DATEPICKER_TAG);
            if (dpd != null) {
                dpd.setOnDateSetListener(this);
            }

            TimePickerDialog tpd = (TimePickerDialog) getSupportFragmentManager().findFragmentByTag(TIMEPICKER_TAG);
            if (tpd != null) {
                tpd.setOnTimeSetListener(this);
            }
        }
*/


        btnSave.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                final Alarm _alarm;

                if (alarm != null) {
                    _alarm = alarm;
                }
                else {
                    _alarm = new Alarm();
                }

                _alarm.setEnabled(enabled.isChecked());

                try {
                    int type = lytTimer.getVisibility() == View.GONE ? Alarm.TYPE_SCHEDULED : Alarm.TYPE_ALARM;

                    _alarm.setType(type);

                    if (type == Alarm.TYPE_ALARM) {
                        EditText timeoutTxt = (EditText) view.findViewById(R.id.timer_timeout);
                        _alarm.setTimeout(Integer.parseInt(timeoutTxt.getText().toString()));

                        EditText messageTxt = (EditText) view.findViewById(R.id.timer_message);
                        if (TextUtils.getTrimmedLength(messageTxt.getText()) > 0) {
                            _alarm.setMessage(messageTxt.getText().toString());
                        }
                    }
                    else {

                        calendar.getTime();

                        _alarm.setTime(calendar.getTime());

                        EditText messageTxt = (EditText) view.findViewById(R.id.scheduled_message);
                        if (TextUtils.getTrimmedLength(messageTxt.getText()) > 0) {
                            _alarm.setMessage(messageTxt.getText().toString());
                        }

                        _alarm.setRepeatEvery(scheduleRepeat.isChecked() ? getTimeInMinutes(spinner) : null);
                    }
                }
                catch (Exception e) {
                    e.printStackTrace();
                    Snackbar.make(view, "Error creating the alarm", Snackbar.LENGTH_LONG)
                            .setAction("Action", null).show();
                }


                IluAlarmConnection conn = new IluAlarmConnection(getContext());

                conn.addCommand(new IluAlarmConnection.IluConnectionJob<Alarm>() {
                    @Override
                    public Response doCall(IluAlarm conn) throws IOException {
                        Call<IluAlarmResponse<Alarm>> call = conn.postAlarm(_alarm);
                        return call.execute();
                    }

                    @Override
                    public void onSuccess(Alarm data) {
                        if (mListener != null) {
                            mListener.onAlarmSaved(data);
                        }
                    }

                    @Override
                    public void onError(Exception e) {
                        e.printStackTrace();
                        Snackbar.make(view, "Error saving the alarm", Snackbar.LENGTH_LONG)
                                .setAction("Action", null).show();
                    }
                });
            }
        });


        return view;
    }

    private Integer getTimeInMinutes(Spinner spinner) {
        switch (spinner.getSelectedItemPosition()) {
            case 0:
                return 10;
            case 1:
                return 60;
            case 2:
                return 60 * 12;
            case 3:
                return 60 * 24;

        }
        return null;
    }

    private Integer getSpinnerPosition(Alarm al) {
        switch (al.getRepeatEvery()) {
            case 10:
                return 0;
            case 60:
                return 1;
            case 60 * 12:
                return 2;
            case 60 * 24:
                return 3;

        }
        return 0;
    }



    @Override
    public void onAttach(Context context) {
        super.onAttach(context);
        if (context instanceof AlarmFragmentListener) {
            mListener = (AlarmFragmentListener) context;
        } else {
            throw new RuntimeException(context.toString()
                    + " must implement AlarmFragmentListener");
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
    public interface AlarmFragmentListener {
        void onAlarmSaved(Alarm alarm);
    }
}
