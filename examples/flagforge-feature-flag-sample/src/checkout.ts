type FlagsmithClient = {
  hasFeature(key: string): boolean;
};

export function checkoutExperience(flagsmith: FlagsmithClient, flagName: string) {
  const redesigned = flagsmith.hasFeature("checkout_v2_redesign");
  const isExperimentEnabled = flagsmith.hasFeature(flagName);

  return {
    layout: redesigned ? "modern" : "classic",
    experimentEnabled: isExperimentEnabled,
  };
}
