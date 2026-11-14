package com.kalabushkin.gym;

import com.mojang.serialization.Codec;
import com.mojang.serialization.codecs.RecordCodecBuilder;

/** Working weight (kg) and reps done at that weight for each exercise. */
public record GymStats(int benchKg, int benchReps, int squatKg, int squatReps, int curlKg, int curlReps) {
	public static final GymStats START = new GymStats(
			Exercise.BENCH.startKg, 0, Exercise.SQUAT.startKg, 0, Exercise.CURL.startKg, 0);

	public static final Codec<GymStats> CODEC = RecordCodecBuilder.create(instance -> instance.group(
			Codec.INT.fieldOf("bench_kg").forGetter(GymStats::benchKg),
			Codec.INT.fieldOf("bench_reps").forGetter(GymStats::benchReps),
			Codec.INT.fieldOf("squat_kg").forGetter(GymStats::squatKg),
			Codec.INT.fieldOf("squat_reps").forGetter(GymStats::squatReps),
			Codec.INT.fieldOf("curl_kg").forGetter(GymStats::curlKg),
			Codec.INT.fieldOf("curl_reps").forGetter(GymStats::curlReps)
	).apply(instance, GymStats::new));

	public int kg(Exercise exercise) {
		return switch (exercise) {
			case BENCH -> benchKg;
			case SQUAT -> squatKg;
			case CURL -> curlKg;
		};
	}

	public int reps(Exercise exercise) {
		return switch (exercise) {
			case BENCH -> benchReps;
			case SQUAT -> squatReps;
			case CURL -> curlReps;
		};
	}

	public GymStats with(Exercise exercise, int kg, int reps) {
		return switch (exercise) {
			case BENCH -> new GymStats(kg, reps, squatKg, squatReps, curlKg, curlReps);
			case SQUAT -> new GymStats(benchKg, benchReps, kg, reps, curlKg, curlReps);
			case CURL -> new GymStats(benchKg, benchReps, squatKg, squatReps, kg, reps);
		};
	}

	/** One level per three weight increases across all exercises. */
	public int strengthLevel() {
		int steps = 0;
		for (Exercise exercise : Exercise.values()) {
			steps += (kg(exercise) - exercise.startKg) / exercise.stepKg;
		}
		return steps / 3;
	}
}
