package com.kalabushkin.gym;

public enum Exercise {
	BENCH("bench", 40, 5, 200),
	SQUAT("squat", 50, 5, 250),
	CURL("curl", 10, 2, 60);

	/** Clean reps at the current working weight before it goes up. */
	public static final int REPS_PER_STEP = 8;

	public final String key;
	public final int startKg;
	public final int stepKg;
	public final int maxKg;

	Exercise(String key, int startKg, int stepKg, int maxKg) {
		this.key = key;
		this.startKg = startKg;
		this.stepKg = stepKg;
		this.maxKg = maxKg;
	}

	public String translationKey() {
		return "gym.kalabushkin.exercise." + key;
	}
}
